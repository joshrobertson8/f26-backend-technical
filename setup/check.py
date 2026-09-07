import argparse
import base64
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"


def run(command, folder):
    if WINDOWS:
        arguments = ["'" + arg.replace("'", "''") + "'" for arg in command]
        script = "& " + " ".join(arguments) + "; exit $LASTEXITCODE"
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]
    return subprocess.run(command, cwd=ROOT / folder, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)


def main():
    python = str(ROOT / "python-fastapi/.venv" / ("Scripts/python.exe" if WINDOWS else "bin/python"))
    options = {
        "python-fastapi": [python, "tests/http_contract.py"],
        "typescript-express": ["npm", "test", "--"],
        "typescript-nextjs": ["npm", "test", "--"],
        "javascript-express": ["npm", "test", "--"],
        "javascript-nextjs": ["npm", "test", "--"],
        "java-spring-boot": ["python3", "test.py"],
        "c": ["python3", "build.py", "test"],
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("option", nargs="?", choices=options)
    args = parser.parse_args()
    selected = [args.option] if args.option else list(options)

    for folder in selected:
        command = options[folder]
        result = run(command, folder)
        print(result.stdout, flush=True)
        unfinished = (
            result.returncode == 1
            and "Passed: 4  |  Failed: 8  |  Errors: 0" in result.stdout
            and "HTTP 501" in result.stdout
        )
        completed = (
            result.returncode == 0
            and "Passed: 12  |  Failed: 0  |  Errors: 0" in result.stdout
        )
        if not (unfinished or completed):
            raise RuntimeError(f"{folder}: the documented test command did not run correctly")
        print(f"[PASS] {folder}: candidate test command works", flush=True)

    print(f"\nAll {len(selected)} selected test commands work.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"\n[ERROR] {error}", file=sys.stderr)
        sys.exit(1)
