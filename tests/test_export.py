"""Scoped Markdown export keeps unrelated saved videos private."""
import json
from unittest.mock import patch

from test_map import VideoMap
from test_ytmd import KEY, y


class ExportVideos(VideoMap):
    def test_export_one_saved_video_by_id_url_or_title(self):
        self.save(KEY, title="Selected tutorial")
        other = "dQw4w9WgXcQ"
        self.save(other, title="Private tutorial")
        for number, selector in enumerate((KEY, y.url_for(KEY), "Selected tutorial")):
            with self.subTest(selector=selector):
                destination = self.root / f"export-{number}"
                with patch.object(y, "fetch", side_effect=AssertionError("network")):
                    result = self.data("export", str(destination), "--video", selector)
                self.assertEqual(result["files"], [str(destination.resolve() / f"{KEY}.md")])
                self.assertIn("Selected tutorial", (destination / f"{KEY}.md").read_text())
                self.assertFalse((destination / f"{other}.md").exists())

    def test_unknown_or_ambiguous_video_does_not_write_files(self):
        self.save(KEY, title="Tutorial one")
        self.save("dQw4w9WgXcQ", title="Tutorial two")
        destination = self.root / "export"
        for selector, expected in (("missing", "not_found"), ("Tutorial", "ambiguous_video")):
            with self.subTest(selector=selector):
                code, out, err = self.call("export", str(destination), "--video", selector)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertEqual(json.loads(err)["error"]["code"], expected)
                self.assertFalse(destination.exists())

    def test_export_without_filter_still_exports_entire_library(self):
        self.save(KEY)
        self.save("dQw4w9WgXcQ")
        destination = self.root / "all"
        result = self.data("export", str(destination))
        self.assertEqual(len(result["files"]), 2)
        self.assertEqual(len(list(destination.glob("*.md"))), 2)

    def test_scoped_export_repairs_default_markdown(self):
        self.save(KEY)
        result = self.data("export", "--video", KEY)
        self.assertEqual(result["files"], [str(y.library() / f"{KEY}.md")])
        self.assertTrue((y.library() / f"{KEY}.md").is_file())
