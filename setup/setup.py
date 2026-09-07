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

