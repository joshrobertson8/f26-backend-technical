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

