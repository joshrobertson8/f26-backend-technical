import contextlib
import importlib.util
import io
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("events_setup", Path(__file__).resolve().parents[1] / "setup.py")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.tools_patch = patch.object(setup, "TOOLS", self.root)
        self.tools_patch.start()
        self.addCleanup(self.tools_patch.stop)
        self.addCleanup(self.directory.cleanup)

    def test_linux_package_managers(self):
        for manager in ["apt-get", "dnf", "yum", "pacman", "zypper", "apk"]:
            with self.subTest(manager=manager):
                commands = setup.package_commands(manager, ["gcc"])
                self.assertEqual(commands[-1][-1], "gcc")
                self.assertEqual(commands[-1][0], manager)

    def test_unsupported_package_manager_is_a_clear_error(self):
        with self.assertRaisesRegex(setup.SetupError, "package manager"):
            setup.package_commands(None, ["gcc"])

