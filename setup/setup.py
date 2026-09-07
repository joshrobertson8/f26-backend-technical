#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.request import Request, urlopen
import zipfile

SETUP = Path(__file__).resolve().parent
ROOT = SETUP.parent
TOOLS = SETUP / ".tools"
ENV = os.environ.copy()
PATHS = []
WINDOWS = os.name == "nt"
SYSTEM = platform.system()

OPTIONS = {
    "python-fastapi": "Python (FastAPI)",
    "javascript-express": "JavaScript (Express)",
    "typescript-express": "TypeScript (Express)",
    "javascript-nextjs": "JavaScript (Next.js)",
    "typescript-nextjs": "TypeScript (Next.js)",
    "java-spring-boot": "Java (Spring Boot)",
    "c": "C",
}


class SetupError(Exception):
    pass


def run(label, command, cwd=ROOT):
    print(f"[RUN] {label}", flush=True)
    log_dir = TOOLS / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / (re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") + ".log")

    with log_file.open("w", encoding="utf-8") as output:
        result = subprocess.run([str(arg) for arg in command], cwd=cwd, env=ENV,
                                stdout=output, stderr=subprocess.STDOUT)

    if result.returncode != 0:
        lines = log_file.read_text(errors="replace").splitlines()
        detail = "\n".join(lines[-35:])
        raise SetupError(f"{label} failed.\n{detail}\nFull log: {log_file}")

    print(f"[ OK] {label}", flush=True)


def capture(command):
    try:
        result = subprocess.run([str(arg) for arg in command], env=ENV,
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout + result.stderr
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


def add_path(directory):
    directory = str(directory)
    if directory not in PATHS:
        PATHS.append(directory)
    ENV["PATH"] = os.pathsep.join(PATHS + [os.environ.get("PATH", "")])


def find(name):
    return shutil.which(name, path=ENV.get("PATH"))


def fetch(url):
    request = Request(url, headers={"User-Agent": "F26-events-setup"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=90) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2)


def download(url, filename, checksum):
    cache = TOOLS / "downloads"
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / Path(filename).name

    if destination.exists():
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest == checksum:
            return destination

    print(f"[GET] {filename}", flush=True)
    data = fetch(url)
    if hashlib.sha256(data).hexdigest() != checksum:
        raise SetupError(f"Checksum mismatch for {filename}; download was not installed.")

    destination.write_bytes(data)
    return destination


def unpack(archive, destination):
    with tempfile.TemporaryDirectory(dir=TOOLS, prefix="unpack-") as name:
        staging = Path(name)

        def inside(path):
            try:
                path.resolve().relative_to(staging.resolve())
                return True
            except ValueError:
                return False

        if archive.suffix == ".zip":
            with zipfile.ZipFile(archive) as bundle:
                for item in bundle.infolist():
                    if not inside(staging / item.filename):
                        raise SetupError("Unsafe path in downloaded ZIP archive.")
                bundle.extractall(staging)
        else:
            with tarfile.open(archive) as bundle:
                for item in bundle.getmembers():
                    target = staging / item.name
                    if not inside(target) or item.isdev() or item.isfifo():
                        raise SetupError("Unsafe path in downloaded tar archive.")
                    if item.issym() and not inside(target.parent / item.linkname):
                        raise SetupError("Unsafe symbolic link in downloaded archive.")
                    if item.islnk() and not inside(staging / item.linkname):
                        raise SetupError("Unsafe hard link in downloaded archive.")
                if hasattr(tarfile, "data_filter"):
                    bundle.extractall(staging, filter="data")
                else:
                    bundle.extractall(staging)

        children = list(staging.iterdir())
        if len(children) != 1 or not children[0].is_dir():
            raise SetupError("Unexpected tool archive layout.")

        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(children[0]), destination)


def architecture():
    machine = platform.machine().lower()
    if machine in ["x86_64", "amd64"]:
        return "x64"
    if machine in ["aarch64", "arm64"]:
        return "arm64"
    raise SetupError(f"Unsupported CPU: {machine}. Use a 64-bit x64 or ARM64 machine.")


def install_node():
    for directory in [TOOLS / "node", TOOLS / "node/bin"]:
        if directory.is_dir():
            add_path(directory)

    node = find("node")
    version = capture([node, "--version"]) if node else ""
    numbers = re.search(r"v(\d+)\.(\d+)", version)
    npm = find("npm")
    npm_cli = None

    if npm:
        npm_path = Path(npm).resolve()
        if npm_path.name == "npm-cli.js":
            npm_cli = npm_path
        else:
            candidate = npm_path.parent / "node_modules/npm/bin/npm-cli.js"
            if candidate.is_file():
                npm_cli = candidate

    if numbers and tuple(map(int, numbers.groups())) >= (20, 9) and npm_cli:
        add_path(Path(node).parent)
        print(f"[ OK] Node.js {version.strip()}")
        return Path(node), npm_cli

    if SYSTEM == "Linux" and Path("/etc/alpine-release").exists():
        install_packages(["nodejs", "npm"])
        node = find("node")
        npm = find("npm")
        npm_cli = Path(npm).resolve() if npm else None
        version = capture([node, "--version"]) if node else ""
        numbers = re.search(r"v(\d+)\.(\d+)", version)
        if not numbers or tuple(map(int, numbers.groups())) < (20, 9) or not npm_cli:
            raise SetupError("This Alpine release needs a newer nodejs/npm package (Node 20.9+).")
        return Path(node), npm_cli

    target = {"Darwin": "darwin", "Linux": "linux", "Windows": "win"}[SYSTEM]
    extension = "zip" if WINDOWS else "tar.gz"
    base = "https://nodejs.org/dist/latest-v22.x/"
    checksums = fetch(base + "SHASUMS256.txt").decode().splitlines()
    suffix = f"-{target}-{architecture()}.{extension}"

    for line in checksums:
        digest, filename = line.split()
        if filename.endswith(suffix):
            archive = download(base + filename, filename, digest)
            unpack(archive, TOOLS / "node")
            break
    else:
        raise SetupError("No compatible Node.js 22 download was found.")

    node_dir = TOOLS / "node" if WINDOWS else TOOLS / "node/bin"
    add_path(node_dir)
    node = node_dir / ("node.exe" if WINDOWS else "node")
    npm_cli = TOOLS / "node/node_modules/npm/bin/npm-cli.js" if WINDOWS else TOOLS / "node/lib/node_modules/npm/bin/npm-cli.js"
    if not capture([node, "--version"]) or not npm_cli.is_file():
        raise SetupError("The downloaded Node.js runtime could not run on this OS.")
    return node, npm_cli


def java_home_is_valid(home):
    javac = home / "bin" / ("javac.exe" if WINDOWS else "javac")
    java = home / "bin" / ("java.exe" if WINDOWS else "java")
    match = re.search(r"javac (\d+)", capture([javac, "-version"]))
    return match and 17 <= int(match.group(1)) <= 25 and bool(capture([java, "-version"]))


def install_java():
    candidates = [TOOLS / "java", TOOLS / "java/Contents/Home"]
    if ENV.get("JAVA_HOME"):
        candidates.append(Path(ENV["JAVA_HOME"]))

    java = find("java")
    if java:
        properties = capture([java, "-XshowSettings:properties", "-version"])
        match = re.search(r"^\s*java.home = (.+)$", properties, re.MULTILINE)
        if match:
            candidates.append(Path(match.group(1).strip()))

    for home in candidates:
        if java_home_is_valid(home):
            ENV["JAVA_HOME"] = str(home)
            add_path(home / "bin")
            print(f"[ OK] {capture([home / 'bin/javac', '-version']).strip()}")
            return home

    if SYSTEM == "Linux" and Path("/etc/alpine-release").exists():
        install_packages(["openjdk21-jdk"])
        home = Path("/usr/lib/jvm/java-21-openjdk")
    else:
        target = {"Darwin": "mac", "Linux": "linux", "Windows": "windows"}[SYSTEM]
        arch = "aarch64" if architecture() == "arm64" else "x64"
        url = f"https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture={arch}&image_type=jdk&os={target}&vendor=eclipse"
        assets = json.loads(fetch(url))
        if not assets:
            raise SetupError("No compatible Temurin JDK 21 download was found.")
        package = assets[0]["binary"]["package"]
        archive = download(package["link"], package["name"], package["checksum"])
        unpack(archive, TOOLS / "java")
        home = TOOLS / "java/Contents/Home" if SYSTEM == "Darwin" else TOOLS / "java"

    if not java_home_is_valid(home):
        raise SetupError("The installed JDK could not run. A JDK, including javac, is required.")
    ENV["JAVA_HOME"] = str(home)
    add_path(home / "bin")
    return home


def package_commands(manager, packages):
    if manager == "apt-get":
        return [[manager, "update"], [manager, "install", "-y"] + packages]
    if manager in ["dnf", "yum"]:
        return [[manager, "install", "-y"] + packages]
    if manager == "pacman":
        return [[manager, "-S", "--needed", "--noconfirm"] + packages]
    if manager == "zypper":
        return [[manager, "--non-interactive", "install"] + packages]
    if manager == "apk":
        return [[manager, "add", "--no-cache"] + packages]
    raise SetupError("No supported Linux package manager found (apt, dnf, yum, pacman, zypper, apk).")


def install_packages(packages):
    manager = next((name for name in ["apt-get", "dnf", "yum", "pacman", "zypper", "apk"] if find(name)), None)
    prefix = []
    if os.geteuid() != 0:
        sudo = find("sudo")
        if not sudo:
            raise SetupError("Administrator access is needed to install system packages; sudo is unavailable.")
        subprocess.run([sudo, "-v"], check=True)
        prefix = [sudo]
    for command in package_commands(manager, packages):
        run("Install system packages", prefix + command)


def compiler_works(compiler):
    if not compiler:
        return False
    with tempfile.TemporaryDirectory(dir=TOOLS, prefix="compiler-check-") as name:
        directory = Path(name)
        source = directory / "check.c"
        binary = directory / ("check.exe" if WINDOWS else "check")
        source.write_text("#include <stdio.h>\nint main(void) { puts(\"compiler-ok\"); return 0; }\n")
        command = [str(compiler), str(source), "-o", str(binary)]
        try:
            result = subprocess.run(command, env=ENV, capture_output=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return False
        if result.returncode != 0:
            return False
        return "compiler-ok" in capture([binary])


def install_compiler():
    candidates = [ENV.get("CC"), find("cc"), find("gcc"), find("clang")]
    if WINDOWS:
        msys_root = Path(ENV.get("MSYS2_ROOT", "C:/msys64"))
        subdir = "clangarm64" if architecture() == "arm64" else "ucrt64"
        compiler_name = "clang.exe" if subdir == "clangarm64" else "gcc.exe"
        directory = msys_root / subdir / "bin"
        if directory.exists():
            add_path(directory)
            candidates.insert(0, str(directory / compiler_name))

    for compiler in candidates:
        if compiler and Path(compiler).is_file() and compiler_works(compiler):
            ENV["CC"] = str(compiler)
            print(f"[ OK] C compiler: {compiler}")
            return

    if SYSTEM == "Darwin":
        print("[WAIT] Complete the Xcode Command Line Tools installer if it opens.", flush=True)
        subprocess.run(["xcode-select", "--install"], check=False)
        deadline = time.monotonic() + 3600
        while time.monotonic() < deadline:
            compiler = find("cc")
            if compiler and compiler_works(compiler):
                ENV["CC"] = compiler
                return
            time.sleep(10)
        raise SetupError("Xcode Command Line Tools are not ready. Finish the installer and rerun setup.")

    if SYSTEM == "Linux":
        manager = next((name for name in ["apt-get", "dnf", "yum", "pacman", "zypper", "apk"] if find(name)), None)
        packages = ["gcc", "make"]
        if manager == "apt-get":
            packages = ["build-essential"]
        elif manager == "apk":
            packages = ["build-base"]
        elif manager in ["dnf", "yum", "zypper"]:
            packages += ["glibc-devel"]
        install_packages(packages)
    else:
        winget = find("winget")
        if not winget:
            candidate = Path(ENV.get("LOCALAPPDATA", "")) / "Microsoft/WindowsApps/winget.exe"
            winget = str(candidate) if candidate.is_file() else None
        if not winget:
            run("Install Windows Package Manager", ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", SETUP / "setup.ps1", "-WinGetOnly"])
            winget = find("winget")
            if not winget:
                candidate = Path(ENV.get("LOCALAPPDATA", "")) / "Microsoft/WindowsApps/winget.exe"
                winget = str(candidate) if candidate.is_file() else None
        if not winget:
            raise SetupError("Windows Package Manager did not install. Restart Windows and rerun setup/setup.cmd.")
        msys_root = Path(ENV.get("MSYS2_ROOT", "C:/msys64"))
        bash = msys_root / "usr/bin/bash.exe"
        if not bash.is_file():
            run("Install MSYS2", [winget, "install", "--id", "MSYS2.MSYS2", "--exact", "--source", "winget", "--architecture", architecture(), "--silent", "--accept-package-agreements", "--accept-source-agreements", "--location", msys_root])
        if not bash.is_file():
            raise SetupError(f"MSYS2 was not found at {msys_root}. Set MSYS2_ROOT to its installation directory.")
        ENV["MSYSTEM"] = "CLANGARM64" if architecture() == "arm64" else "UCRT64"
        ENV["CHERE_INVOKING"] = "1"
        run("Initialize MSYS2", [bash, "-lc", "true"])
        run("Update MSYS2 core", [bash, "-lc", "pacman --noconfirm -Syuu"])
        run("Update MSYS2 packages", [bash, "-lc", "pacman --noconfirm -Syuu"])
        package = "mingw-w64-clang-aarch64-clang" if architecture() == "arm64" else "mingw-w64-ucrt-x86_64-gcc"
        run("Install Windows C compiler", [bash, "-lc", f"pacman --noconfirm -S --needed {package}"])
        subdir = "clangarm64" if architecture() == "arm64" else "ucrt64"
        add_path(msys_root / subdir / "bin")

    for name in ["cc", "gcc", "clang"]:
        compiler = find(name)
        if compiler and compiler_works(compiler):
            ENV["CC"] = compiler
            return
    raise SetupError("C compiler installation did not produce a working compiler and linker.")


def python_runtime():
    python = Path(getattr(sys, "_base_executable", sys.executable)).resolve()
    if not (3, 9) <= sys.version_info[:2] < (3, 14):
        raise SetupError("Use Python 3.9–3.13. The bootstrap scripts install Python 3.12 when needed.")

    return python


def prepare_python():
    python = python_runtime()
    venv = ROOT / "python-fastapi/.venv"
    executable = venv / ("Scripts/python.exe" if WINDOWS else "bin/python")
    compatible = capture([executable, "-c", "import sys; print('ready') if (3, 9) <= sys.version_info[:2] < (3, 14) else sys.exit(1)"])
    if venv.exists() and "ready" not in compatible:
        backup = venv.with_name(f".venv-backup-{int(time.time())}")
        venv.rename(backup)
        print(f"[INFO] Moved an incompatible virtual environment to {backup.name}")
    if not executable.is_file() or not capture([executable, "-m", "pip", "--version"]):
        try:
            run("Create Python virtual environment", [python, "-m", "venv", venv])
        except SetupError:
            if SYSTEM != "Linux":
                raise
            manager = next((name for name in ["apt-get", "dnf", "yum", "pacman", "zypper", "apk"] if find(name)), None)
            if manager == "apt-get":
                install_packages(["python3-venv", "python3-pip"])
            else:
                install_packages(["python3-pip"] if manager != "pacman" else ["python-pip"])
            run("Create Python virtual environment", [python, "-m", "venv", venv])
    run("Install FastAPI dependencies", [executable, "-m", "pip", "install", "-r", ROOT / "python-fastapi/requirements.txt"])
    return python, executable


def write_activation(python, java_home=None, compiler=None, venv=None):
    if venv is not None:
        python = venv / ("Scripts/python.exe" if WINDOWS else "bin/python")

    bin_dir = TOOLS / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name in ["python", "python3"]:
        if WINDOWS:
            (bin_dir / (name + ".cmd")).write_text('@echo off\n"%F26_PYTHON%" %*\n', encoding="ascii")
        else:
            shim = bin_dir / name
            if shim.is_symlink() or shim.exists():
                shim.unlink()
            shim.symlink_to(python)
    add_path(bin_dir)
    PATHS.remove(str(bin_dir))
    PATHS.insert(0, str(bin_dir))

    if venv is not None:
        venv_bin = str(python.parent)
        if venv_bin in PATHS:
            PATHS.remove(venv_bin)
        PATHS.insert(0, venv_bin)

    ENV["PATH"] = os.pathsep.join(PATHS + [os.environ.get("PATH", "")])
    values = {"F26_PYTHON": str(python)}

    if venv is not None:
        values["VIRTUAL_ENV"] = str(venv)

    if java_home is not None:
        values["JAVA_HOME"] = str(java_home)

