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

    def test_failed_step_does_not_report_success(self):
        with patch.object(setup.subprocess, "run") as run:
            run.return_value.returncode = 7
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaisesRegex(setup.SetupError, "Example step failed"):
                    setup.run("Example step", ["missing-command"])
        self.assertNotIn("[ OK]", output.getvalue())

    def test_windows_activation_preserves_unicode_paths(self):
        with patch.object(setup, "WINDOWS", True), patch.object(setup, "PATHS", []), patch.object(setup, "ENV", {"CC": "C:/Tools/gcc.exe"}):
            setup.write_activation(Path("C:/Café O'Neil/python.exe"), Path("C:/Tools/jdk"))
        script = self.root / "activate.ps1"
        self.assertTrue(script.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertIn("Café O''Neil/python.exe", script.read_text(encoding="utf-8-sig").replace("\\", "/"))
        self.assertTrue((self.root / "bin/python3.cmd").read_bytes().isascii())

    def test_incompatible_virtual_environment_is_backed_up(self):
        project = self.root / "python-fastapi"
        old_venv = project / ".venv"
        old_venv.mkdir(parents=True)
        (old_venv / "keep.txt").write_text("existing environment")
        with patch.object(setup, "ROOT", self.root), patch.object(setup, "capture", return_value=""), patch.object(setup, "run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                setup.prepare_python()
        backups = list(project.glob(".venv-backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "keep.txt").read_text(), "existing environment")
        self.assertEqual(run.call_args_list[0].args[0], "Create Python virtual environment")

    def test_unresponsive_compiler_is_not_selected(self):
        error = setup.subprocess.TimeoutExpired("cc", 30)
        with patch.object(setup.subprocess, "run", side_effect=error):
            self.assertFalse(setup.compiler_works("cc"))

    @unittest.skipIf(setup.WINDOWS, "POSIX activation uses symbolic links")
    def test_setup_resolves_its_python_alias_before_replacing_it(self):
        real_python = self.root / "runtime/python"
        real_python.parent.mkdir()
        real_python.write_text("test executable")
        alias = self.root / "python3"
        alias.symlink_to(real_python)
        with patch.object(setup, "ROOT", self.root), patch.object(setup.sys, "_base_executable", str(alias)), patch.object(setup, "capture", return_value=""), patch.object(setup, "run"):
            python, _ = setup.prepare_python()
        self.assertEqual(python, real_python.resolve())

    def test_menu_lists_full_names_and_selects_each_option(self):
        for number, folder in enumerate(setup.OPTIONS, start=1):
            with self.subTest(folder=folder):
                with patch("builtins.input", return_value=str(number)):
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        self.assertEqual(setup.choose_option([]), folder)
                for name in setup.OPTIONS.values():
                    self.assertIn(name, output.getvalue())

    def test_menu_retries_invalid_input(self):
        with patch("builtins.input", side_effect=["invalid", "0", "8", "2"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(setup.choose_option([]), "javascript-express")

    def test_menu_handles_missing_input(self):
        with patch("builtins.input", side_effect=EOFError):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(setup.SetupError, "No selection"):
                    setup.choose_option([])

    def test_invalid_option_does_not_install_anything(self):
        with patch.object(setup, "python_runtime") as runtime:
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    setup.main(["unknown"])
        self.assertEqual(error.exception.code, 2)
        runtime.assert_not_called()

    def test_activation_does_not_require_java_or_a_compiler(self):
        with patch.object(setup, "WINDOWS", True), patch.object(setup, "PATHS", []):
            setup.write_activation(Path("C:/Tools/python.exe"))
        script = (self.root / "activate.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("F26_PYTHON", script)
        self.assertNotIn("JAVA_HOME", script)
        self.assertNotIn("$env:CC", script)

    def test_each_option_only_prepares_its_own_dependencies(self):
        for folder in setup.OPTIONS:
            with self.subTest(folder=folder), contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(setup, "ROOT", self.root))
                stack.enter_context(patch.object(setup, "ENV", {"CC": "compiler"}))
                stack.enter_context(patch.object(setup, "architecture", return_value="x64"))
                stack.enter_context(patch.object(setup, "python_runtime", return_value=Path("python")))
                python = stack.enter_context(patch.object(setup, "prepare_python", return_value=(Path("python"), Path("venv/python"))))
                node = stack.enter_context(patch.object(setup, "install_node", return_value=(Path("node"), Path("npm"))))
                java = stack.enter_context(patch.object(setup, "install_java", return_value=Path("jdk")))
                compiler = stack.enter_context(patch.object(setup, "install_compiler"))
                activation = stack.enter_context(patch.object(setup, "write_activation"))
                run = stack.enter_context(patch.object(setup, "run"))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

                setup.main([folder])

                self.assertEqual((self.root / "selected-folder.txt").read_text().strip(), folder)
                self.assertEqual(python.call_count, int(folder == "python-fastapi"))
                self.assertEqual(java.call_count, int(folder == "java-spring-boot"))
                self.assertEqual(compiler.call_count, int(folder == "c"))
                self.assertEqual(node.call_count, int(folder.startswith(("javascript-", "typescript-"))))
                activation.assert_called_once()
                self.assertEqual(run.call_args.args[0], "Check " + folder)
                self.assertEqual(run.call_args.args[2], self.root / folder)
                for call in run.call_args_list:
                    if call.args[0].startswith(("Install ", "Build ")) and folder != "c":
                        self.assertEqual(call.args[2], self.root / folder)

    def test_windows_python_selection_activates_its_virtual_environment(self):
        venv = self.root / "python environment"
        with patch.object(setup, "WINDOWS", True), patch.object(setup, "PATHS", []), patch.object(setup, "ENV", {}):
            setup.write_activation(Path("C:/Python/python.exe"), venv=venv)
            self.assertEqual(setup.PATHS[0], str(venv / "Scripts"))

        script = (self.root / "activate.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("$env:VIRTUAL_ENV =", script)
        self.assertIn(str(venv / "Scripts/python.exe"), script)

    @unittest.skipIf(setup.WINDOWS, "POSIX shell handoff")
    def test_python_commands_use_the_selected_virtual_environment(self):
        venv = self.root / "python environment"
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)

        with patch.object(setup, "PATHS", []), patch.object(setup, "ENV", {}):
            setup.write_activation(Path(sys.executable), venv=venv)

        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-c", 'source "$1"; python -c "import sys; print(sys.prefix)"', "bash", str(self.root / "activate.sh")],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(Path(result.stdout.strip()).resolve(), venv.resolve())

    @unittest.skipIf(setup.WINDOWS, "POSIX terminal handoff")
    def test_setup_opens_a_terminal_with_tools_already_active(self):
        import pty

        project = self.root / "events workspace"
        project.mkdir()
        installer = project / "setup"
        installer.mkdir()
        challenge = project / "python-fastapi"
        challenge.mkdir()
        (challenge / "candidate.txt").write_text("correct-challenge-directory\n")
        shutil.copyfile(setup.SETUP / "setup.sh", installer / "setup.sh")
        (installer / "setup.py").write_text(
            'from pathlib import Path\n'
            'tools = Path(__file__).parent / ".tools"\n'
            '(tools / "activate.sh").write_text("export CANDIDATE_READY=ready-after-setup\\n")\n'
            '(tools / "selected-folder.txt").write_text("python-fastapi\\n")\n'
        )

        pid, terminal = pty.fork()
        if pid == 0:
            os.chdir(project)
            os.execvp("bash", ["bash", "setup/setup.sh"])

