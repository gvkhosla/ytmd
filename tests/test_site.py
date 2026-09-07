"""Static website checks; no Node dependencies or network access required."""
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.elements = []
        self.ids = {}
        self.text = defaultdict(str)
        self.stack = []

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        self.elements.append((tag, attrs))
        key = attrs.get("id")
        if key:
            if key in self.ids:
                raise ValueError("Duplicate ID: " + key)
            self.ids[key] = (tag, attrs)
        if tag not in self.VOID:
            self.stack.append((tag, key))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        for _, key in self.stack:
            if key:
                self.text[key] += data


class LandingPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = Document()
        cls.doc.feed((SITE / "index.html").read_text())
        cls.readme = (ROOT / "README.md").read_text()

    def test_local_assets_and_anchors_exist(self):
        for tag, attrs in self.doc.elements:
            for field in ("src", "href"):
                value = attrs.get(field, "")
                if not value:
                    continue
                parsed = urlparse(value)
                if parsed.scheme or parsed.netloc:
                    continue
                if parsed.path:
                    self.assertFalse(parsed.path.startswith("/"), "Use relative paths for GitHub project Pages")
                    self.assertTrue((SITE / unquote(parsed.path)).exists(), value)
                if parsed.fragment:
                    self.assertIn(parsed.fragment, self.doc.ids)
        for path in re.findall(r"url\(['\"]?([^)'\"]+)", (SITE / "style.css").read_text()):
            self.assertTrue((SITE / path).exists(), path)

    def test_copy_targets_and_accessible_controls(self):
        copies = []
        for tag, attrs in self.doc.elements:
            if "data-copy" in attrs:
                self.assertEqual(tag, "button")
                self.assertEqual(attrs.get("type"), "button")
                self.assertIn(attrs["data-copy"], self.doc.ids)
                self.assertTrue(self.doc.text[attrs["data-copy"]].strip())
                copies.append(attrs["data-copy"])
        self.assertEqual(set(copies), {"install-code", "agent-prompt", "use-prompt"})
        self.assertEqual(self.doc.ids["copy-status"][1]["role"], "status")
        self.assertEqual(self.doc.ids["copy-status"][1]["aria-live"], "polite")

    def test_install_commands_match_readme_and_release(self):
        commands = self.doc.text["install-code"].strip()
        self.assertIn("```bash\n" + commands + "\n```", self.readme)
        self.assertIn("```bash\n" + commands.replace("brew install python yt-dlp", "pipx install yt-dlp") + "\n```", self.readme)
        version = re.search(r'^VERSION = "([^"]+)"', (ROOT / "ytmd").read_text(), re.M).group(1)
        self.assertIn(f"/v{version}/install.sh", commands)
        self.assertIn("--agent all", commands)
        self.assertNotIn("sudo", commands)

    def test_no_external_scripts_or_stylesheets(self):
        for tag, attrs in self.doc.elements:
            if tag == "script" or (tag == "link" and attrs.get("rel") in ("stylesheet", "preload")):
                resource = attrs.get("src", attrs.get("href", ""))
                self.assertFalse(urlparse(resource).netloc, resource)

    def test_share_metadata_and_image(self):
        meta = {attrs.get("property", attrs.get("name")): attrs.get("content") for tag, attrs in self.doc.elements if tag == "meta"}
        self.assertEqual(meta["og:url"], "https://gvkhosla.github.io/ytmd/")
        self.assertEqual(meta["twitter:card"], "summary_large_image")
        self.assertEqual(meta["og:image"], meta["twitter:image"])
        image = SITE / "assets/social.png"
        data = image.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (1200, 630))

    def test_semantic_structure(self):
        self.assertEqual(sum(tag == "h1" for tag, _ in self.doc.elements), 1)
        self.assertEqual(sum(tag == "main" for tag, _ in self.doc.elements), 1)
        for tag, attrs in self.doc.elements:
            if tag == "img":
                self.assertIn("alt", attrs)
            if tag == "nav":
                self.assertIn("aria-label", attrs)
        self.assertIn("<noscript>", (SITE / "index.html").read_text())

    def test_setup_prompt_matches_readme(self):
        prompt = " ".join(self.doc.text["agent-prompt"].split())
        self.assertIn(prompt, " ".join(self.readme.split()))


if __name__ == "__main__":
    unittest.main()
