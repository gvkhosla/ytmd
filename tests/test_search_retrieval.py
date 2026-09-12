"""Search selection, context merging, and citation preservation (offline)."""
import json
import shlex

from test_ytmd import Isolated, KEY, row, y

SECOND = "dQw4w9WgXcQ"
THIRD = "7TKqQ2hyM5k"


def hit(start, end, text, score=-1, key=KEY):
    return dict(video_id=key, title="Test", captions="manual", lang="en", caption_format="json3",
                start=start, end=end, text=text, score=score, url=y.url_for(key, start))


class SearchRetrieval(Isolated):
    def seed_video(self, key, cues, channel="Test"):
        y.save(self.db(), dict(row(cues), id=key, url=y.url_for(key), channel=channel,
                              duration_s=max(c["end"] for c in cues)))

    def search(self, *flags):
        p = self.cli("search", "needle", *flags, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, "")
        return json.loads(p.stdout)

    def test_overlapping_windows_merge_and_preserve_best_hit_and_citations(self):
        self.seed_video(KEY, [dict(start=10, end=12, text="needle alpha"),
                              dict(start=20, end=22, text="needle beta"),
                              dict(start=500, end=502, text="needle distant")])
        raw = self.search("-n", "3")
        merged = self.search("--context", "15", "-n", "3")
        self.assertEqual(len(raw), 3)
        self.assertEqual(len(merged), 2)
        cluster = next(r for r in merged if "matches" in r)
        original = next(r for r in raw if r["start"] in (10, 20))
        for key, value in original.items():
            self.assertEqual(cluster[key], value)
        self.assertEqual([m["start"] for m in cluster["matches"]], [10, 20])
        for match in cluster["matches"]:
            source = next(r for r in raw if r["start"] == match["start"])
            self.assertEqual(match, {k: source[k] for k in ("start", "end", "text", "url", "score")})
        self.assertEqual(cluster["context"]["text"].count("needle alpha"), 1)
        self.assertEqual(cluster["context"]["text"].count("needle beta"), 1)
        self.assertNotIn("distant", cluster["context"]["text"])
        self.assertEqual((cluster["context"]["start"], cluster["context"]["end"]), (10, 22))
        self.assertEqual(cluster["context"]["url"], y.url_for(KEY, 10))
        self.assertNotIn("matches", next(r for r in merged if r["start"] == 500))

    def test_transitive_overlap_is_order_independent_and_keeps_best_root(self):
        cues = [dict(start=t, end=t + 2, text=f"text {t}") for t in (0, 10, 20, 30, 40)]
        strongest = hit(20, 22, "text 20", score=-3)
        raw = [strongest, hit(40, 42, "text 40", score=-2), hit(0, 2, "text 0")]
        merged = y.merge_search_context(raw, {KEY: cues}, 15)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["start"], 20)
        self.assertEqual(merged[0]["score"], -3)
        self.assertEqual([m["start"] for m in merged[0]["matches"]], [0, 20, 40])
        self.assertEqual(merged[0]["context"]["text"], y.transcript(cues))
        self.assertNotIn("context", strongest)  # Input hits aren't mutated.

    def test_repeated_speech_is_not_deduplicated(self):
        cues = [dict(start=t, end=t + 2, text="Yes, needle.") for t in (0, 10)]
        merged = y.merge_search_context([hit(0, 2, cues[0]["text"]), hit(10, 12, cues[1]["text"])], {KEY: cues}, 15)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["context"]["text"].count("Yes, needle."), 2)

    def test_zero_duration_boundary_cues_survive_merging(self):
        cues = [dict(start=0, end=0, text="First"), dict(start=0, end=0, text="Second")]
        merged = y.merge_search_context([hit(0, 0, "First"), hit(0, 0, "Second")], {KEY: cues}, 1)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["context"]["text"], y.transcript(cues))
        self.assertEqual(merged[0]["context"]["end"], 0)

    def test_different_videos_never_merge_even_with_identical_text_and_timing(self):
        cues = [dict(start=0, end=2, text="needle"), dict(start=10, end=12, text="needle again")]
        for key in (KEY, SECOND):
            self.seed_video(key, cues)
        merged = self.search("--context", "15", "-n", "4")
        self.assertEqual(len(merged), 2)
        self.assertEqual({r["video_id"] for r in merged}, {KEY, SECOND})
        self.assertTrue(all(len(r["matches"]) == 2 for r in merged))
        for result in merged:
            self.assertTrue(all(f"v={result['video_id']}" in m["url"] for m in result["matches"]))

    def test_zero_context_retains_individual_hit_shape_and_limit(self):
        self.seed_video(KEY, [dict(start=0, end=2, text="needle"), dict(start=10, end=12, text="needle again")])
        results = self.search("--context", "0", "-n", "2")
        self.assertEqual(len(results), 2)
        self.assertTrue(all("context" not in r and "matches" not in r for r in results))
        limited = self.search("--context", "15", "-n", "1")
        self.assertEqual(len(limited), 1)
        self.assertNotIn("matches", limited[0])  # -n limits selected hits before merging.

    def test_diverse_round_robins_in_best_video_order(self):
        raw = [hit(0, 1, "A1", -9), hit(10, 11, "A2", -8),
               hit(0, 1, "B1", -7, SECOND), hit(20, 21, "A3", -6),
               hit(10, 11, "B2", -5, SECOND), hit(0, 1, "C1", -4, THIRD)]
        selected = y.diverse_hits(iter(raw), 5)
        self.assertEqual([r["text"] for r in selected], ["A1", "B1", "C1", "A2", "B2"])
        self.assertEqual(y.diverse_hits(iter([]), 5), [])

    def test_diverse_stops_after_enough_distinct_videos(self):
        def rows():
            yield hit(0, 1, "A")
            yield hit(0, 1, "B", key=SECOND)
            raise AssertionError("Unneeded rows consumed")
        self.assertEqual(len(y.diverse_hits(rows(), 2)), 2)

    def test_diverse_does_not_hide_videos_beyond_a_large_global_top_pool(self):
        self.seed_video(KEY, [dict(start=i * 60, end=i * 60 + 2, text="needle needle needle") for i in range(1001)])
        self.seed_video(SECOND, [dict(start=0, end=2, text="needle " + "filler " * 100)])
        default = self.search("-n", "3")
        self.assertEqual([r["video_id"] for r in default], [KEY, KEY, KEY])
        diverse = self.search("--diverse", "-n", "3")
        self.assertEqual([r["video_id"] for r in diverse], [KEY, SECOND, KEY])
        self.assertEqual(diverse[0], default[0])
        self.assertEqual(diverse[2], default[1])
        self.assertEqual(diverse, self.search("--diverse", "-n", "3"))

    def test_diverse_respects_video_and_channel_filters(self):
        cues = [dict(start=0, end=2, text="needle"), dict(start=60, end=62, text="needle again")]
        self.seed_video(KEY, cues, "Channel A")
        self.seed_video(SECOND, cues, "Channel B")
        for flags in (("--video", KEY), ("--channel", "Channel A")):
            with self.subTest(flags=flags):
                filtered = self.search("--diverse", *flags, "-n", "3")
                self.assertEqual(len(filtered), 2)
                self.assertTrue(all(r["video_id"] == KEY for r in filtered))
        self.assertEqual(self.search("--diverse", "--channel", "No such channel"), [])

    def test_diversity_and_merging_work_together(self):
        cues = [dict(start=0, end=2, text="needle"), dict(start=10, end=12, text="needle again")]
        for key in (KEY, SECOND):
            self.seed_video(key, cues)
        merged = self.search("--diverse", "--context", "15", "-n", "4")
        self.assertEqual(len(merged), 2)
        self.assertEqual({r["video_id"] for r in merged}, {KEY, SECOND})
        self.assertTrue(all(len(r["matches"]) == 2 for r in merged))

    def test_human_next_command_covers_merged_context(self):
        cues = [dict(start=0, end=2, text="needle"),
                dict(start=100, end=102, text="needle repeated"),
                dict(start=200, end=202, text="needle ending")]
        self.seed_video(KEY, cues)
        p = self.cli("search", "needle", "--context", "120")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.count("needle repeated"), 1)
        self.assertEqual(p.stdout.count("needle ending"), 1)
        self.assertIn("3 matches", p.stdout)
        command = shlex.split(p.stdout.rsplit("Next: ", 1)[1])
        self.assertEqual(command, ["ytmd", "show", KEY, "--from", "0:00", "--to", "3:22"])
        empty = self.cli("search", "unmatched", "--context", "15", "--diverse", "--json")
        self.assertEqual(json.loads(empty.stdout), [])

    def test_diverse_flag_is_documented_and_rejects_a_value(self):
        self.assertIn("--diverse", self.cli("help", "search").stdout)
        p = self.cli("search", "needle", "--diverse=false", "--json")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stderr)["error"]["code"], "usage")
