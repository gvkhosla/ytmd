"""Packaging metadata stays aligned with the CLI version."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Packaging(unittest.TestCase):
    def test_pyproject_version_matches_cli(self):
        cli = (ROOT / "ytmd").read_text()
        pyproject = (ROOT / "pyproject.toml").read_text()
        cli_version = re.search(r'(?m)^VERSION = "([^"]+)"', cli)
        name = re.search(r'(?m)^name = "([^"]+)"', pyproject)
        version = re.search(r'(?m)^version = "([^"]+)"', pyproject)
        requires = re.search(r'(?m)^requires-python = "([^"]+)"', pyproject)
        self.assertIsNotNone(cli_version)
        self.assertIsNotNone(name)
        self.assertIsNotNone(version)
        self.assertEqual(name.group(1), "ytmd")
        self.assertEqual(version.group(1), cli_version.group(1))
        self.assertIn("3.9", requires.group(1))

    def test_homebrew_formula_pins_the_release_tag_and_depends_on_ytdlp(self):
        formula = (ROOT / "Formula" / "ytmd.rb").read_text()
        self.assertIn("tag: \"v0.7.0\"", formula)
        self.assertIn("head \"https://github.com/gvkhosla/ytmd.git\"", formula)
        self.assertIn("depends_on \"yt-dlp\"", formula)
        self.assertIn("bin.install_symlink", formula)

    def test_release_checksums_match_payloads(self):
        for line in (ROOT / "SHA256SUMS").read_text().splitlines():
            expected, name = line.split()
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)
