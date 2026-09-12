"""Offline dependency/version and PATH diagnostics."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

from test_ytmd import Isolated, y


class Doctor(Isolated):
    def diagnostics(self, version, returncode=0):
        result = subprocess.CompletedProcess([], returncode, version, "")
        with patch.object(y.subprocess, "run", return_value=result) as run, patch.object(y, "datetime") as clock:
            clock.now.return_value = datetime(2026, 9, 12, tzinfo=timezone.utc)
            clock.strptime.side_effect = datetime.strptime
            data = y.ytdlp_diagnostics("/bin/yt-dlp")
        run.assert_called_once_with(["/bin/yt-dlp", "--ignore-config", "--version"], capture_output=True, text=True, timeout=5)
        return data

    def test_old_dependency_warns_without_updating(self):
        version, age, warnings = self.diagnostics("2026.02.04\n")
        self.assertEqual(version, "2026.02.04")
        self.assertGreater(age, 90)
        self.assertEqual(warnings[0]["code"], "yt_dlp_outdated")
        self.assertIn("no update was performed", warnings[0]["message"])

    def test_recent_and_future_releases_do_not_warn(self):
        for value in ("2026.09.12", "2026.09.12.123456", "2027.01.01"):
            with self.subTest(value=value):
                version, age, warnings = self.diagnostics(value)
                self.assertEqual(version, value)
                self.assertEqual(age, 0)
                self.assertEqual(warnings, [])

    def test_ninety_day_boundary(self):
        self.assertEqual(self.diagnostics("2026.06.14")[1:], (90, []))
        self.assertEqual(self.diagnostics("2026.06.13")[2][0]["code"], "yt_dlp_outdated")

    def test_unknown_versions_and_failed_commands_are_advisory(self):
        for version, status in (("", 0), ("custom build", 0), ("2026.99.99", 0), ("2026.09.12", 1)):
            with self.subTest(version=version, status=status):
                _, age, warnings = self.diagnostics(version, status)
                self.assertIsNone(age)
                self.assertEqual(warnings[0]["code"], "yt_dlp_version_unknown")

    def test_timeout_and_os_error_are_advisory(self):
        for error in (subprocess.TimeoutExpired("yt-dlp", 5), OSError("not executable")):
            with self.subTest(error=error), patch.object(y.subprocess, "run", side_effect=error):
                version, age, warnings = y.ytdlp_diagnostics("/bin/yt-dlp")
                self.assertIsNone(version)
                self.assertIsNone(age)
                self.assertEqual(warnings[0]["code"], "yt_dlp_version_unknown")

    def test_missing_dependency_does_not_run_a_command(self):
        with patch.object(y.subprocess, "run") as run:
            self.assertEqual(y.ytdlp_diagnostics(None), (None, None, []))
        run.assert_not_called()

    def test_path_order_and_duplicate_entries(self):
        first, second = self.root / "first", self.root / "second"
        first.mkdir()
        second.mkdir()
        for directory in (first, second):
            (directory / "ytmd").write_text("#!/bin/sh\n")
            (directory / "ytmd").chmod(0o755)
        with patch.dict(os.environ, {"PATH": os.pathsep.join(map(str, (second, first, second)))}):
            self.assertEqual(y.executable_paths("ytmd"), [str(second / "ytmd"), str(first / "ytmd")])
        (first / "ytmd").chmod(0o644)
        with patch.dict(os.environ, {"PATH": str(first)}):
            self.assertEqual(y.executable_paths("ytmd"), [])

    def doctor_data(self, paths, binary="/bin/yt-dlp"):
        out = io.StringIO()
        with patch.object(y, "executable_paths", return_value=paths), patch.object(y.shutil, "which", return_value=binary), patch.object(y, "ytdlp_diagnostics", return_value=("2026.09.12", 0, [])), redirect_stdout(out):
            code = y.main(["doctor", "--json"])
        self.assertFalse(y.library().exists())
        return code, json.loads(out.getvalue())

    def test_multiple_installations_include_active_script_and_path_order(self):
        first, second = self.root / "first", self.root / "second"
        code, data = self.doctor_data([str(first), str(second)])
        self.assertEqual(code, 0)
        self.assertTrue(data["ok"])
        self.assertEqual(data["executable"], str(Path(y.__file__).resolve()))
        self.assertEqual(data["ytmd_on_path"], [{"path": str(p), "resolved": str(p.resolve())} for p in (first, second)])
        self.assertEqual(data["warnings"][0]["code"], "multiple_installations")
        self.assertIn(str(first), data["warnings"][0]["message"])

    def test_symlinks_to_one_installation_do_not_warn(self):
        binary = self.root / "actual"
        binary.write_text("test")
        alias = self.root / "alias"
        alias.symlink_to(binary)
        code, data = self.doctor_data([str(alias), str(binary)])
        self.assertEqual(code, 0)
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["ytmd_on_path"][0]["resolved"], str(binary.resolve()))

    def test_missing_binary_still_fails_health_check(self):
        code, data = self.doctor_data([], binary=None)
        self.assertEqual(code, 1)
        self.assertFalse(data["ok"])

    def test_real_cli_uses_only_local_version_command_and_keeps_json_clean(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "yt-dlp"
        stub.write_text('#!/bin/sh\n[ "$1" = "--ignore-config" ] && [ "$2" = "--version" ] && [ "$#" = "2" ] || exit 9\nprintf "2000.01.01\\n"\n')
        stub.chmod(0o755)
        with patch.dict(os.environ, {"PATH": str(bin_dir)}):
            result = self.cli("doctor", "--json")
            human = self.cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        data = json.loads(result.stdout)
        self.assertEqual(data["yt_dlp_version"], "2000.01.01")
        self.assertEqual(data["warnings"][0]["code"], "yt_dlp_outdated")
        self.assertIn("Warnings (advisory):", human.stdout)
        self.assertIn("executable:", human.stdout)
        self.assertFalse(y.library().exists())
