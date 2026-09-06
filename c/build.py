#!/usr/bin/env python3
"""Build, run, or test the C option on Windows, macOS, or Linux."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BINARY = ROOT / "build" / ("server.exe" if os.name == "nt" else "server")


def build(sanitize=False):
    compiler = os.environ.get("CC")

    if not compiler:
        for name in ["cc", "gcc", "clang"]:
            compiler = shutil.which(name)
            if compiler:
                break

    if not compiler:
        raise RuntimeError("C compiler missing. Run the root setup script first.")

    sources = [ROOT / "src" / name for name in [
        "controller.c", "models.c", "server.c", "service.c", "store.c",
    ]]
    sources += [ROOT / "vendor/cJSON.c", ROOT / "vendor/picohttpparser.c"]
    BINARY.parent.mkdir(exist_ok=True)

    command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Wno-unused-parameter", "-O0", "-g"]
    command += ["-I", str(ROOT / "include"), "-I", str(ROOT / "vendor")]
    command += [str(source) for source in sources]

    if sanitize:
        if os.name == "nt":
            raise RuntimeError("Sanitizer mode is available on macOS/Linux.")
        command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]

    if os.name == "nt":
        command += ["-lws2_32"]

    command += ["-o", str(BINARY)]
    print("Building C server...", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    print("C server built.", flush=True)

