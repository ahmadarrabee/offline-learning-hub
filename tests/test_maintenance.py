import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "maintenance" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backup = load("auto_backup")
diagnostics = load("system_diagnostics")


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "data"
        self.source.mkdir()
        (self.source / "database.sqlite3").write_bytes(b"sample offline data")
        self.mount = self.root / "usb"
        self.mount.mkdir()
        self.target = self.mount / "kolibri_backups"

    def run_backup(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return backup.create_backup(self.source, self.target, self.mount)

    def test_success_and_unique_snapshots(self):
        with patch.object(Path, "is_mount", return_value=True):
            first = self.run_backup()
            second = self.run_backup()
        self.assertNotEqual(first, second)
        self.assertEqual((first / "database.sqlite3").read_bytes(), b"sample offline data")
        self.assertEqual(len(list(self.target.iterdir())), 2)
        self.assertFalse(any(p.name.endswith(".partial") for p in self.target.iterdir()))

    def test_unmounted_usb_rejected_without_creating_target(self):
        with patch.object(Path, "is_mount", return_value=False):
            with self.assertRaises(OSError):
                self.run_backup()
        self.assertFalse(self.target.exists())

    def test_missing_source(self):
        with self.assertRaises(FileNotFoundError):
            backup.create_backup(self.root / "missing", self.target, self.mount)

    def test_target_outside_mount(self):
        with patch.object(Path, "is_mount", return_value=True):
            with self.assertRaises(ValueError):
                backup.create_backup(self.source, self.root / "outside", self.mount)

    def test_overlapping_source_and_destination(self):
        with patch.object(Path, "is_mount", return_value=True):
            with self.assertRaises(ValueError):
                backup.create_backup(self.mount, self.target, self.mount)

    def test_failed_copy_never_published_as_complete(self):
        def fail_copy(source, target, **kwargs):
            target.mkdir()
            (target / "incomplete").write_text("partial")
            raise OSError("USB full")
        with patch.object(Path, "is_mount", return_value=True), patch.object(shutil, "copytree", side_effect=fail_copy):
            with self.assertRaises(OSError):
                self.run_backup()
        self.assertEqual(len(list(self.target.iterdir())), 1)
        self.assertTrue(next(self.target.iterdir()).name.endswith(".partial"))


class DiagnosticTests(unittest.TestCase):
    def test_service_states(self):
        for state, code, expected in [("active", 0, True), ("inactive", 3, False), ("failed", 3, False), ("unknown", 4, False)]:
            with self.subTest(state=state), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], code, state, "")):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(diagnostics.check_service_status(), expected)

    def test_systemctl_missing_or_timed_out(self):
        for error in [FileNotFoundError("systemctl"), subprocess.TimeoutExpired("systemctl", 10)]:
            with patch.object(subprocess, "run", side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(diagnostics.check_service_status())

    def test_disk_breakdown(self):
        with patch.object(shutil, "disk_usage", return_value=(10 * 1024**3, 4 * 1024**3, 6 * 1024**3)):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                diagnostics.check_disk_space()
            for amount in ["10.00 GiB", "4.00 GiB", "6.00 GiB"]:
                self.assertIn(amount, stream.getvalue())


if __name__ == "__main__":
    unittest.main()
