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

