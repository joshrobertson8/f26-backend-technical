import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main():
    print("Building Java project...", flush=True)

