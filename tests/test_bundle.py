"""Multi-video evidence bundles."""
import json
from unittest.mock import patch

from test_map import VideoMap
from test_ytmd import KEY, y

SECOND = "dQw4w9WgXcQ"
THIRD = "7TKqQ2hyM5k"


class BundleBehavior(VideoMap):
    def test_explicit_sources_and_queries_are_required(self):
        self.save(KEY)
        code, out, err = self.call("bundle", "--query", "cache")
        self.assertEqual(code, 2)
        self.assertIn("explicit", json.loads(err)["error"]["message"])
        code, out, err = self.call("bundle", KEY, SECOND, "--library", "--query", "cache")
        self.assertEqual(code, 2)
        code, out, err = self.call("bundle", "missing11id", "--query", "cache")
        self.assertEqual(json.loads(err)["error"]["code"], "not_found")
        self.assertEqual(out, "")

    def test_missing_selector_fails_before_partial_bundle(self):
        self.save(KEY)
        code, out, err = self.call("bundle", KEY, SECOND, "--query", "cache")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(json.loads(err)["error"]["code"], "not_found")

    def test_duplicate_selectors_are_deduped_in_order(self):
        self.save(KEY)
        self.save(SECOND, cues=[dict(start=0, end=2, text="other cache")])
        data = self.data("bundle", KEY, KEY, SECOND, "--query", "cache")
        self.assertEqual(data["scope"]["video_ids"], [KEY, SECOND])
        self.assertEqual(data["scope"]["mode"], "explicit")

    def test_one_prolific_video_cannot_consume_the_whole_budget(self):
        self.save(KEY, cues=[dict(start=0, end=10, text="cache " * 400)])
        self.save(SECOND, cues=[dict(start=0, end=10, text="cache isolation note")])
        data = self.data("bundle", KEY, SECOND, "--query", "cache", "--max-chars", "256", "--context", "0")
        sources = {item["ref"]["video_id"] for item in data["evidence"]}
        self.assertEqual(sources, {KEY, SECOND})
        self.assertEqual(data["budget"]["used_chars"], 256)
        self.assertTrue(data["omissions"]["budget_exhausted"])
        self.assertIn(KEY, data["omissions"]["sources_omitted_by_budget"])

    def test_repeated_speech_stays_distinct(self):
        text = "Yes, sandbox isolation."
        self.save(KEY, cues=[dict(start=0, end=2, text=text), dict(start=90, end=92, text=text)])
        data = self.data("bundle", KEY, "--query", "sandbox", "--context", "0")
        self.assertEqual([e["start"] for e in data["evidence"]], [0, 90])
        self.assertEqual(data["evidence"][0]["text"], data["evidence"][1]["text"])
        self.assertNotEqual(data["evidence"][0]["id"], data["evidence"][1]["id"])

    def test_unmatched_query_is_disclosed_not_absence(self):
        self.save(KEY)
        data = self.data("bundle", KEY, "--query", "unicorn")
        self.assertEqual(data["evidence"], [])
        self.assertEqual(data["retrieval"]["unmatched_queries"], ["unicorn"])
        self.assertIn("not prove", data["coverage_note"])
        self.assertFalse(data["omissions"]["selection_is_exhaustive"])

    def test_library_mode_is_offline_and_capped(self):
        for i, key in enumerate((KEY, SECOND, THIRD)):
            self.save(key, cues=[dict(start=0, end=2, text=f"cache video {i}")], title=f"Talk {i}")
        with patch.object(y, "fetch", side_effect=AssertionError("network fetch")), patch.object(y, "run_ytdlp", side_effect=AssertionError("yt-dlp")):
            data = self.data("bundle", "--library", "--query", "cache")
        self.assertEqual(data["scope"]["mode"], "library")
        self.assertEqual(set(data["scope"]["video_ids"]), {KEY, SECOND, THIRD})

    def test_equivalent_calls_are_deterministic(self):
        self.save(KEY)
        self.save(SECOND, cues=[dict(start=10, end=12, text="cache rollback")])
        first = self.data("bundle", KEY, SECOND, "--query", "cache", "--query", "rollback")
        second = self.data("bundle", KEY, SECOND, "--query", "cache", "--query", "rollback")
        self.assertEqual(first["evidence"], second["evidence"])
        self.assertEqual([e["id"] for e in first["evidence"]], [e["id"] for e in second["evidence"]])

    def test_write_refuses_existing_file_without_overwrite(self):
        self.save(KEY)
        path = self.root / "bundle.json"
        path.write_text("old")
        code, out, err = self.call("bundle", KEY, "--query", "cache", "--out", str(path))
        self.assertEqual(json.loads(err)["error"]["code"], "file_exists")
        self.assertEqual(path.read_text(), "old")
        data = self.data("bundle", KEY, "--query", "cache", "--out", str(path), "--overwrite")
        saved = json.loads(path.read_text())
        self.assertEqual(saved["kind"], "ytmd_evidence_bundle")
        self.assertEqual(saved["evidence"], data["evidence"])
        self.assertEqual(data["path"], str(path.resolve()))
