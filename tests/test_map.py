"""Section maps for chaptered and chapterless videos."""
import json
import shlex
from unittest.mock import patch

from test_read_context import ReadingAndEvidence
from test_ytmd import Isolated, KEY, row, y


class VideoMap(Isolated):
    def save(self, key=KEY, cues=None, chapters=None, duration=130, title="A tutorial"):
        record = row(cues)
        record.update(id=key, title=title, url=y.url_for(key), duration_s=duration,
                      chapters_json=json.dumps(chapters) if chapters is not None else None)
        if chapters is None:
            record["description"] = "No timestamps in this description."
        conn = y.connect()
        try:
            y.save(conn, record)
        finally:
            conn.close()
        return record


VideoMap.call = ReadingAndEvidence.call
VideoMap.data = ReadingAndEvidence.data


class MapBehavior(VideoMap):
    def test_publisher_chapters_are_not_reinterpreted(self):
        self.save(chapters=[dict(start=0, end=60, title="Introduction"), dict(start=60, end=130, title="Technique")])
        data = self.data("map", KEY)
        self.assertEqual(data["section_kind"], "publisher_chapters")
        self.assertEqual([s["title"] for s in data["sections"]], ["Introduction", "Technique"])
        self.assertEqual(data["sections"][1]["read_command"], f"ytmd read {KEY} --chapter 2 --json")
        self.assertIn("not publisher chapters", data["coverage_note"])
        self.assertFalse(data["has_more"])
        chapter = self.data(*data["sections"][1]["read_command"].split()[1:-1])
        self.assertEqual(chapter["scope"]["chapter"], 2)

    def test_chapterless_video_gets_five_minute_time_sections(self):
        cues = [dict(start=t, end=t + 2, text=f"word {t}") for t in range(0, 601, 60)]
        self.save(cues=cues, chapters=None, duration=600)
        data = self.data("map", KEY)
        self.assertEqual(data["section_kind"], "generated_time_sections")
        self.assertEqual([(s["start"], s["end"]) for s in data["sections"]], [(0.0, 300.0), (300.0, 600.0)])
        self.assertTrue(all("–" in s["title"] for s in data["sections"]))
        self.assertIn("--from", data["sections"][0]["read_command"])
        self.assertNotIn("--chapter", data["sections"][0]["read_command"])
        read = self.data(*data["sections"][0]["read_command"].split()[1:-1])
        self.assertEqual(read["scope"]["start"], 0)
        self.assertEqual(read["scope"]["end"], 300)

    def test_preview_budget_is_shared_across_sections(self):
        cues = [dict(start=0, end=10, text="alpha " * 80), dict(start=300, end=310, text="beta " * 80)]
        self.save(cues=cues, chapters=None, duration=600)
        data = self.data("map", KEY, "--max-chars", "256")
        self.assertEqual(data["preview_budget"]["used_chars"], 256)
        self.assertTrue(all(s["preview"] for s in data["sections"]))
        self.assertLessEqual(sum(len(s["preview"]) for s in data["sections"]), 256)
        self.assertTrue(any(s["preview_truncated"] for s in data["sections"]))

    def test_empty_section_is_labelled_not_filled(self):
        self.save(cues=[dict(start=0, end=2, text="only intro")], chapters=None, duration=600)
        data = self.data("map", KEY)
        empty = next(s for s in data["sections"] if s["start"] == 300)
        self.assertTrue(empty["empty"])
        self.assertEqual(empty["preview"], "")
        self.assertEqual(empty["caption_chars"], 0)

    def test_map_paginates_section_metadata(self):
        self.save(cues=[dict(start=0, end=1, text="x")], chapters=None, duration=1800)
        data = self.data("map", KEY, "--limit", "2")
        self.assertEqual(data["total_sections"], 6)
        self.assertEqual(len(data["sections"]), 2)
        self.assertTrue(data["has_more"])
        self.assertIn("--offset 2", data["next_command"])
        page = self.data(*shlex.split(data["next_command"])[1:-1])
        self.assertEqual(page["offset"], 2)
        self.assertEqual(page["sections"][0]["number"], 3)

    def test_missing_duration_uses_caption_end(self):
        self.save(cues=[dict(start=0, end=12, text="short")], chapters=None, duration=None)
        data = self.data("map", KEY)
        self.assertEqual(data["sections"][0]["end"], 12)

    def test_map_does_not_fetch(self):
        self.save()
        with patch.object(y, "fetch", side_effect=AssertionError("network fetch")):
            self.data("map", KEY)
