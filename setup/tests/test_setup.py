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

    def test_cpu_names(self):
        for machine, expected in [("AMD64", "x64"), ("x86_64", "x64"), ("arm64", "arm64"), ("aarch64", "arm64")]:
            with self.subTest(machine=machine), patch.object(setup.platform, "machine", return_value=machine):
                self.assertEqual(setup.architecture(), expected)

    def test_bad_checksum_is_not_installed(self):
        with patch.object(setup, "fetch", return_value=b"bad download"):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(setup.SetupError, "Checksum"):
                    setup.download("https://example.invalid/tool.zip", "tool.zip", "0" * 64)
        self.assertFalse((self.root / "downloads/tool.zip").exists())

    def test_archive_path_cannot_escape(self):
        archive = self.root / "unsafe.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            entry = tarfile.TarInfo("../outside.txt")
            entry.size = 3
            bundle.addfile(entry, io.BytesIO(b"bad"))
        with self.assertRaisesRegex(setup.SetupError, "Unsafe"):
            setup.unpack(archive, self.root / "tool")

    def test_archive_external_link_is_rejected(self):
        archive = self.root / "unsafe-link.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            entry = tarfile.TarInfo("tool/link")
            entry.type = tarfile.SYMTYPE
            entry.linkname = "../../outside"
            bundle.addfile(entry)
        with self.assertRaisesRegex(setup.SetupError, "Unsafe"):
            setup.unpack(archive, self.root / "tool")

    def test_windows_activation_has_python_aliases_and_quoted_paths(self):
        with patch.object(setup, "WINDOWS", True), patch.object(setup, "PATHS", []), patch.object(setup, "ENV", {"CC": "C:/Some Tools/gcc.exe"}):
            setup.write_activation(Path("C:/Some Tools/python.exe"), Path("C:/Some Tools/jdk"), "C:/Some Tools/gcc.exe")
        script = (self.root / "activate.ps1").read_text(encoding="utf-8-sig").replace("\\", "/")
        self.assertIn("$env:JAVA_HOME = 'C:/Some Tools/jdk'", script)
        self.assertIn("$env:CC = 'C:/Some Tools/gcc.exe'", script)
        self.assertIn("$env:F26_PYTHON = 'C:/Some Tools/python.exe'", script)
        self.assertIn('"%F26_PYTHON%" %*', (self.root / "bin/python3.cmd").read_text())

