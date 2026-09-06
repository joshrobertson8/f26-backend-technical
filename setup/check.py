import argparse
import base64
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"

