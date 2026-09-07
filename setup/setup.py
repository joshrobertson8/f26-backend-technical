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

