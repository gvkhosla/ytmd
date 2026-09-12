"""Offline caption import."""
import json
from unittest.mock import patch

from test_map import VideoMap
from test_ytmd import KEY, y


class ImportCaptions(VideoMap):
    def test_vtt_json3_and_srt_round_trip(self):
        vtt = self.root / "captions.vtt"
        vtt.write_bytes(b"\xef\xbb\xbfWEBVTT\r\n\r\n00:00:00.000 --> 00:00:02.000\r\nFirst line\r\nSecond line\r\n")
        data = self.data("import", str(vtt), "--video", KEY, "--title", "Imported talk")
        self.assertEqual(data["status"], "imported")
        self.assertEqual(data["captions"], "user_supplied")
        self.assertTrue(data["duration_derived"])
        read = self.data("read", KEY)
        self.assertEqual(read["passages"][0]["text"], "First line Second line")
        self.assertEqual(read["captions"], "user_supplied")

        srt = self.root / "captions.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:01,500\nYes <i>cache</i>\n\n2\n00:00:10,000 --> 00:00:11,000\nYes <i>cache</i>\n")
        other = "dQw4w9WgXcQ"
        srt_data = self.data("import", str(srt), "--video", other, "--title", "SRT")
        self.assertEqual(srt_data["caption_format"], "srt")
        bundled = self.data("bundle", other, "--query", "cache", "--context", "0")
        self.assertEqual([e["start"] for e in bundled["evidence"]], [0, 10])

        json3 = self.root / "captions.json3"
        json3.write_text(json.dumps({"events": [{"tStartMs": 0, "dDurationMs": 1000, "segs": [{"utf8": "Use List<T>"}]}]}))
        third = "7TKqQ2hyM5k"
        self.data("import", str(json3), "--video", third, "--title", "JSON3")
        self.assertIn("List<T>", self.data("read", third)["passages"][0]["text"])

    def test_existing_source_requires_force_and_failed_parse_does_not_replace(self):
        self.save(KEY)
        path = self.root / "captions.vtt"
        path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello cache\n")
        code, out, err = self.call("import", str(path), "--video", KEY, "--title", "Nope")
        self.assertEqual(json.loads(err)["error"]["code"], "already_saved")
        self.assertEqual(self.data("read", KEY)["title"], "A tutorial")
        bad = self.root / "bad.vtt"
        bad.write_text("WEBVTT\n\nnot a timestamp\n")
        code, out, err = self.call("import", str(bad), "--video", KEY, "--title", "Bad", "--force")
        self.assertEqual(json.loads(err)["error"]["code"], "invalid_captions")
        self.assertEqual(self.data("read", KEY)["title"], "A tutorial")
        self.data("import", str(path), "--video", KEY, "--title", "Replaced", "--force")
        self.assertEqual(self.data("read", KEY)["title"], "Replaced")
        self.assertEqual(self.data("read", KEY)["captions"], "user_supplied")

    def test_import_does_not_call_ytdlp(self):
        path = self.root / "captions.vtt"
        path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello\n")
        with patch.object(y, "fetch", side_effect=AssertionError("network")), patch.object(y, "run_ytdlp", side_effect=AssertionError("yt-dlp")):
            self.data("import", str(path), "--video", KEY, "--title", "Local")
        self.data("map", KEY)
        self.data("search", "Hello")
