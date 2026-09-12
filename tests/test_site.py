"""Static website checks; no Node dependencies or network access required."""
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import re
import json
import runpy
import shlex
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
        cls.videos = json.loads((ROOT / 'examples/videos.json').read_text())['videos']

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
        self.assertEqual(copies, ["agent-prompt"], 'Keep one primary copy action')
        self.assertEqual(self.doc.ids["copy-status"][1]["role"], "status")
        self.assertEqual(self.doc.ids["copy-status"][1]["aria-live"], "polite")

    def test_install_commands_match_readme_and_release(self):
        blocks = re.findall(r'```bash\n(.*?)\n```', self.readme, re.S)
        commands = next(b for b in blocks if b.startswith('brew install'))
        linux = next(b for b in blocks if b.startswith('pipx install'))
        self.assertEqual(linux, commands.replace('brew install python yt-dlp', 'pipx install yt-dlp'))
        self.assertTrue(any(a.get('href') == 'https://github.com/gvkhosla/ytmd#install' for _, a in self.doc.elements), 'Terminal setup remains one link away')
        version = re.search(r'^VERSION = "([^"]+)"', (ROOT / "ytmd").read_text(), re.M).group(1)
        self.assertIn(f"/v{version}/install.sh", commands)
        self.assertIn("--agent all", commands)
        self.assertNotIn("sudo", commands)
        # Fresh pipx installs may not yet be on PATH when the installer checks yt-dlp.
        self.assertLess(commands.index('export PATH='), commands.index('sh /tmp/install-ytmd.sh'))

    def test_agent_guide_is_static_and_versioned(self):
        text = (SITE / "llms.txt").read_text()
        version = re.search(r'^VERSION = "([^"]+)"', (ROOT / "ytmd").read_text(), re.M).group(1)
        self.assertIn(f"/v{version}/install.sh", text)
        self.assertIn("--context", text)
        self.assertIn("language_mismatch", text)
        self.assertIn("untrusted", text)
        links = [attrs for tag, attrs in self.doc.elements if tag == "link"]
        self.assertTrue(any(a.get("rel") == "alternate" and a.get("type") == "text/plain" and a.get("href") == "./llms.txt" for a in links))

    def test_documented_workflow_commands_still_parse(self):
        cli = runpy.run_path(str(ROOT / 'ytmd'), run_name='site_check')
        blocks = re.findall(r'```bash\n(.*?)\n```', self.readme, re.S)
        workflow = next(b for b in blocks if b.startswith('ytmd add'))
        for command in workflow.splitlines():
            args = shlex.split(command)
            self.assertEqual(args[0], 'ytmd')
            self.assertIn(cli['parser']().parse_args(args[1:]).command, ('add', 'info', 'context', 'read'))

    def test_no_external_scripts_or_stylesheets(self):
        for tag, attrs in self.doc.elements:
            if tag in ("script", "img", "iframe") or (tag == "link" and attrs.get("rel") in ("stylesheet", "preload")):
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

    def test_v05_task_prompt_and_discovery_links(self):
        text = (SITE / "index.html").read_text()
        self.assertIn('ytmd gives your AI agent YouTube captions, saved as local Markdown + SQLite.', self.doc.text['main'])
        self.assertIn('not just a summary', self.doc.text['main'])
        structured = re.search(r'<script type="application/ld\+json">(.*?)</script>', text).group(1)
        schema = json.loads(structured)
        self.assertEqual(schema["name"], "ytmd")
        self.assertEqual(schema["softwareVersion"], re.search(r'^VERSION = "([^"]+)"', (ROOT / "ytmd").read_text(), re.M).group(1))
        self.assertIn("examples/README.md", text)
        self.assertTrue((ROOT / "examples/README.md").exists())
        self.assertTrue((ROOT / "evals/README.md").exists())
        self.assertIn("https://gvkhosla.github.io/ytmd/", (SITE / "sitemap.xml").read_text())

    def test_six_real_videos_have_balanced_categories_and_quotes(self):
        self.assertEqual(len(self.videos), 6)
        self.assertEqual(len({v['id'] for v in self.videos}), 6)
        self.assertEqual(sum(v['category'] == 'technical' for v in self.videos), 3)
        self.assertEqual(sum(v['category'] == 'business' for v in self.videos), 3)
        self.assertIn('MZ14rrkHVbg', {v['id'] for v in self.videos})
        self.assertIn('Dwarkesh Patel', {v['channel'] for v in self.videos})
        for video in self.videos:
            self.assertRegex(video['id'], r'^[A-Za-z0-9_-]{11}$')
            evidence = self.doc.text['evidence-' + video['id']]
            for excerpt in video['evidence']:
                self.assertIn(excerpt['quote'], evidence)
                self.assertGreaterEqual(excerpt['start'], 0)
                self.assertLess(excerpt['start'], video['duration_s'])
            self.assertLessEqual(sum(len(e['quote'].split()) for e in video['evidence']), 60)
            self.assertIn(video['coverage'], evidence)
            self.assertIn('captions; may contain errors.', evidence)
            self.assertEqual(len(video['plan']), 3)
            self.assertLessEqual(len(video['result'].split()), 25)
            image = SITE / 'assets/videos' / (video['id'] + '.jpg')
            self.assertEqual(image.read_bytes()[:2], b'\xff\xd8')
            self.assertLess(image.stat().st_size, 150000)
        self.assertNotIn('synthetic', self.doc.text['use'])
        self.assertIn('Plans are our adaptations', self.doc.text['use'])
        self.assertIn('not speaker instructions or full-video reviews', self.doc.text['use'])

    def test_real_timestamps_and_native_disclosures(self):
        citations = [a['href'] for tag, a in self.doc.elements if a.get('class') == 'citation']
        expected = [f"https://www.youtube.com/watch?v={v['id']}&t={int(e['start'])}s"
                    for v in self.videos for e in v['evidence']]
        self.assertEqual(citations, expected)
        for video in self.videos:
            tag, attrs = self.doc.ids['plan-' + video['id']]
            self.assertEqual(tag, 'details')
            self.assertNotIn('open', attrs)
            self.assertNotIn('hidden', attrs)
        self.assertNotIn('role="tab"', (SITE / 'index.html').read_text())

    def test_static_examples_match_the_renderer(self):
        renderer = runpy.run_path(str(ROOT / 'tools/render_examples.py'), run_name='site_check')
        self.assertIn(renderer['render'](), (SITE / 'index.html').read_text())

    def test_demo_precedes_installation_and_keeps_terminal_optional(self):
        text = (SITE / 'index.html').read_text()
        self.assertLess(text.index('id="use"'), text.index('id="install"'))
        self.assertEqual(self.doc.ids['install'][0], 'details')
        self.assertNotIn('<input', text, 'Do not imply this static site accepts videos')
        self.assertLess(len(self.doc.text['main'].split()), 1300, 'Six expanded plans must still stay concise')
        script = (SITE / 'app.js').read_text()
        self.assertNotIn('fetch(', script)
        self.assertNotIn('.innerHTML', script)

    def test_technical_explanation_is_short_and_specific(self):
        text = (SITE / 'index.html').read_text()
        section = re.search(r'<section class="how-it-works"[^>]*>(.*?)</section>', text, re.S).group(1)
        words = re.sub(r'<[^>]+>', ' ', section).split()
        self.assertLessEqual(len(words), 80)
        for term in ('SQLite', 'Markdown', 'Full-text search', 'Timestamped', 'FTS5', 'offline'):
            self.assertIn(term, section)
        self.assertIn('Your agent’s model may run elsewhere.', section)
        self.assertLess(text.index('id="use"'), text.index('class="how-it-works"'))
        self.assertLess(text.index('class="how-it-works"'), text.index('class="setup"'))

    def test_theme_bootstraps_before_styles_and_has_accessible_toggle(self):
        text = (SITE / 'index.html').read_text()
        self.assertLess(text.index('src="./theme.js'), text.index('rel="stylesheet"'))
        tag, attrs = self.doc.ids['theme-toggle']
        self.assertEqual(tag, 'button')
        self.assertEqual(attrs['type'], 'button')
        self.assertEqual(attrs['aria-label'], 'Switch to dark mode')
        self.assertIn('hidden', attrs, 'No inert toggle when JavaScript is disabled')
        self.assertIn('prefers-color-scheme: dark', (SITE / 'style.css').read_text())
        script = (SITE / 'theme.js').read_text()
        self.assertIn("localStorage.setItem('ytmd-theme'", script)
        self.assertNotIn('fetch(', script)
        self.assertNotIn('.innerHTML', script)

    def test_display_font_is_self_hosted_and_licensed(self):
        self.assertTrue((SITE / 'assets/BarlowSemiCondensed-SemiBold.ttf').exists())
        self.assertIn('SIL OPEN FONT LICENSE', (SITE / 'assets/Barlow-OFL.txt').read_text())

    def test_setup_prompt_matches_readme(self):
        prompt = " ".join(self.doc.text["agent-prompt"].split())
        self.assertIn(prompt, " ".join(self.readme.split()))


if __name__ == "__main__":
    unittest.main()
