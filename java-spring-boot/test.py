import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main():
    print("Building Java project...", flush=True)

    command = [
        "java",
        f"-Dmaven.multiModuleProjectDirectory={ROOT}",
        "-classpath",
        str(ROOT / ".mvn/wrapper/maven-wrapper.jar"),
        "org.apache.maven.wrapper.MavenWrapperMain",
        "-q",
        "package",
    ]

    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)

    if build.returncode != 0:
        print("\nRESULT: BUILD FAILED")
        print(build.stdout)
        print(build.stderr)

        return build.returncode

    print("Java project built.\n", flush=True)

    command = [sys.executable, "tests/http_contract.py"] + sys.argv[1:]

    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as error:
        print(f"\nRESULT: ERROR\n{error}", file=sys.stderr)
        print("Run the root setup script first.", file=sys.stderr)
        sys.exit(1)
