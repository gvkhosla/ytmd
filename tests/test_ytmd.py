from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import shlex
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = SourceFileLoader("ytmd", str(ROOT / "ytmd"))
spec = importlib.util.spec_from_loader(loader.name, loader)
y = importlib.util.module_from_spec(spec)
loader.exec_module(y)
KEY = "jNQXAC9IVRw"


def row(cues=None):
    cues = cues or [dict(start=0, end=4, text="Use List<T> to store data."), dict(start=60, end=65, text="Cache invalidation requires care."), dict(start=120, end=124, text="Cache invalidation is hard.")]
    return dict(id=KEY, title="A tutorial", channel="Test", url=y.url_for(KEY), uploaded_at="2026-01-01", duration_s=130, description="Not transcript content", captions="manual", lang="en", ingested_at="2026-09-07T00:00:00Z", transcript=y.transcript(cues), cues_json=json.dumps(cues), raw_captions="original raw fixture", caption_format="json3")


class Isolated(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {"YTMD_DIR": str(self.root / "library")})
        self.env.start()
        self.addCleanup(self.env.stop)

    def db(self):
        conn = y.connect()
        self.addCleanup(conn.close)
        return conn

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "ytmd"), *args], capture_output=True, text=True)


class Parsing(Isolated):
    def test_json3_preserves_technical_notation_and_entities(self):
        raw = json.dumps({"events": [{"tStartMs": 0, "dDurationMs": 1000, "segs": [{"utf8": "Use List<T>, x < y > z &amp; <script>"}]}]})
        self.assertEqual(y.parse_json3(raw)[0]["text"], "Use List<T>, x < y > z &amp; <script>")

    def test_malformed_json3(self):
        for raw in ('{', '[]', '{"events":null}', '{"events":[null]}', '{"events":[{"segs":[{"utf8":null}]}]}'):
            with self.assertRaises(y.Error, msg=raw):
                y.parse_json3(raw)

    def test_vtt_preserves_all_lines(self):
        raw = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nFirst important sentence.\nSecond important sentence.\n"
        self.assertEqual(y.parse_vtt(raw)[0]["text"], "First important sentence. Second important sentence.")

    def test_vtt_markup_and_entities(self):
        raw = "WEBVTT\r\n\r\n1\r\n00:00:00.000 --> 00:00:02.000\r\n<v Speaker><c.green>Use &lt;T&gt; &amp; <b>types</b></c></v>\r\n"
        self.assertEqual(y.parse_vtt(raw)[0]["text"], "Use <T> & types")

    def test_preserves_repeated_speech_and_unknown_angle_brackets(self):
        raw = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nYes <T>.\n\n00:00:10.000 --> 00:00:11.000\nYes <T>.\n"
        cues = y.parse_vtt(raw)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[1]["start"], 10)
        self.assertEqual(cues[1]["text"], "Yes <T>.")

    def test_rollup_requires_evidence(self):
        raw = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000 position:0%\nFirst <00:00:01.000>line\n\n00:00:02.000 --> 00:00:04.000 position:0%\nFirst line\nSecond <00:00:03.000>line\n"
        self.assertEqual([c["text"] for c in y.parse_vtt(raw)], ["First line", "Second line"])

    def test_bad_timing(self):
        with self.assertRaises(y.Error):
            y.validate_cues([dict(start=4, end=3, text="invalid")])
        with self.assertRaises(y.Error):
            y.validate_cues([dict(start=float("nan"), end=3, text="invalid")])

    def test_no_arbitrary_deduplication(self):
        raw = json.dumps({"events": [{"tStartMs": t, "dDurationMs": 1000, "segs": [{"utf8": "Yes"}]} for t in (0, 10000)]})
        self.assertEqual(len(y.parse_json3(raw)), 2)

    def test_url_validation(self):
        for value in (KEY, f"https://youtu.be/{KEY}", f"https://www.youtube.com/watch?v={KEY}&list=abc", f"https://youtube.com/shorts/{KEY}", f"https://youtube.com/live/{KEY}"):
            self.assertEqual(y.video_id(value), KEY)
        for value in (f"https://notyoutube.com/watch?v={KEY}", f"https://youtube.com.evil.test/watch?v={KEY}", f"https://youtube.com@evil.test/watch?v={KEY}", "https://youtube.com/playlist?list=abc", "https://example.com", f"https://youtu.be/{KEY}EXTRA"):
            with self.assertRaises(y.Error, msg=value):
                y.video_id(value)

    def test_track_selection_and_provenance(self):
        fmt = [{"ext": "json3"}]
        info = dict(subtitles={"de": fmt}, automatic_captions={"en": fmt, "en-orig": fmt, "en-de": fmt})
        self.assertEqual(y.choose_track(info), ("en-orig", "auto"))
        info["subtitles"]["en"] = fmt
        self.assertEqual(y.choose_track(info), ("en", "manual"))
        self.assertEqual(y.choose_track(info, "de"), ("de", "manual"))
        with self.assertRaises(y.Error):
            y.choose_track(info, "fr")

    def test_original_fallback_not_random_translation(self):
        fmt = [{"ext": "vtt"}]
        self.assertEqual(y.choose_track(dict(automatic_captions={"fr-orig": fmt, "zu-fr": fmt})), ("fr-orig", "auto"))
        with self.assertRaises(y.Error):
            y.choose_track(dict(automatic_captions={"zu-fr": fmt}))

    def test_ytdlp_error_classifies_gone_videos(self):
        cases = {
            "HTTP Error 429: Too Many Requests": "rate_limited",
            "Sign in to confirm your age": "authentication_required",
            "ERROR: [youtube] 7TKqQ2hyM5k: This video is unavailable": "video_unavailable",
            "ERROR: [youtube] abc: Video unavailable": "video_unavailable",
            "Extractor exploded": "download_failed",
        }
        for detail, code in cases.items():
            with self.subTest(detail=detail):
                with self.assertRaises(y.Error) as raised:
                    y.ytdlp_error(detail)
                self.assertEqual(raised.exception.code, code)

    def test_unavailable_stub_is_not_caption_less(self):
        stub = dict(id=KEY, title=f"youtube video #{KEY}", availability=None, duration=None, channel=None, uploader=None)
        with self.assertRaises(y.Error) as raised:
            y.require_available(stub, KEY)
        self.assertEqual(raised.exception.code, "video_unavailable")
        with self.assertRaises(y.Error) as raised:
            y.require_available(dict(id=KEY, title="Gone", availability="unavailable", duration=12, channel="Test"), KEY)
        self.assertEqual(raised.exception.code, "video_unavailable")
        with self.assertRaises(y.Error) as raised:
            y.require_available(dict(id=KEY, title="Secret", availability="private", duration=12, channel="Test"), KEY)
        self.assertEqual(raised.exception.code, "authentication_required")
        y.require_available(dict(id=KEY, title="A tutorial", duration=130, channel="Test"), KEY)

    def test_missing_metadata_and_placeholder_titles_are_not_proof_of_deletion(self):
        placeholder = f"youtube video #{KEY}"
        cases = [
            {},
            dict(title="A tutorial"),
            dict(title=placeholder, duration=0),
            dict(title=placeholder, channel="Test"),
            dict(title=placeholder, uploader="Test"),
            dict(title=placeholder, formats=[{"format_id": "audio"}]),
            dict(title=placeholder, subtitles={"en": [{"ext": "vtt"}]}),
            dict(title=placeholder, automatic_captions={"en-orig": [{"ext": "json3"}]}),
        ]
        for info in cases:
            with self.subTest(info=info):
                y.require_available(dict(id=KEY, **info), KEY)

    def test_live_metadata_without_duration_is_not_unavailable(self):
        for status in ("is_live", "is_upcoming", "post_live", "was_live"):
            with self.subTest(status=status):
                y.require_available(dict(id=KEY, title=f"youtube video #{KEY}", live_status=status), KEY)

    def test_auth_metadata_takes_precedence_over_empty_stub(self):
        for availability in ("private", "premium_only", "subscriber_only", "needs_auth"):
            with self.subTest(availability=availability):
                with self.assertRaises(y.Error) as raised:
                    y.require_available(dict(title=f"youtube video #{KEY}", availability=availability), KEY)
                self.assertEqual(raised.exception.code, "authentication_required")

    def test_passages_preserve_text_and_split(self):
        cues = json.loads(row()["cues_json"])
        self.assertEqual(len(y.passages(cues)), 3)
        self.assertEqual(" ".join(c["text"] for c in cues), " ".join(c["text"] for c in y.passages(cues)))

    def test_parse_chapters_from_common_description_formats(self):
        dialectic = "Timestamps:\n- (0:00) - Opening Highlights\n- (1:37) - Intro: Miles\n- (1:04:54) - Craft and Trust\n"
        chapters = y.parse_chapters(dialectic, 6788)
        self.assertEqual([(c["start"], c["title"]) for c in chapters], [(0, "Opening Highlights"), (97, "Intro: Miles"), (3894, "Craft and Trust")])
        self.assertEqual(chapters[0]["end"], 97)
        self.assertEqual(chapters[-1]["end"], 6788)
        yc = "Chapters:\n00:00 — Intro\n00:07 — What Should You Still Learn?\n02:01 — Knowledge Still Matters\n"
        self.assertEqual([c["title"] for c in y.parse_chapters(yc)], ["Intro", "What Should You Still Learn?", "Knowledge Still Matters"])
        plain = "00:00 Rewriting Postgres\n02:54 Michael’s background\n"
        self.assertEqual([c["start"] for c in y.parse_chapters(plain)], [0, 174])
        self.assertEqual(y.parse_chapters("Meet at 10:00 AM\nCall at 11:00 PM"), [])
        self.assertEqual(y.parse_chapters("00:00 Intro only"), [])

    def test_player_chapters_preferred_over_description(self):
        info = dict(chapters=[dict(start_time=0, end_time=10, title="A"), dict(start_time=10, end_time=20, title="B")])
        self.assertEqual([c["title"] for c in y.chapters_from_player(info, "00:00 From desc\n00:05 Also desc", 20)], ["A", "B"])
        self.assertEqual([c["title"] for c in y.chapters_from_player({}, "00:00 From desc\n00:05 Also desc", 20)], ["From desc", "Also desc"])


class StorageAndCLI(Isolated):
    def seed(self):
        conn = self.db()
        y.save(conn, row())
        return conn

    def test_migration_backs_up_and_preserves_legacy_transcript(self):
        root = y.library()
        root.mkdir()
        old = sqlite3.connect(root / "ytmd.db")
        old.execute("CREATE TABLE videos (id TEXT PRIMARY KEY, title TEXT, channel TEXT, url TEXT, uploaded_at TEXT, duration_s INTEGER, description TEXT, captions TEXT, lang TEXT, ingested_at TEXT, transcript TEXT)")
        original = row()
        original["transcript"] = "[0:00] Legacy text.\n\n[1:00] Cache invalidation."
        fields = list(original)[:11]
        old.execute("INSERT INTO videos VALUES (" + ",".join("?" for _ in fields) + ")", [original[k] for k in fields])
        old.commit()
        old.close()
        conn = self.db()
        migrated = dict(conn.execute("SELECT * FROM videos").fetchone())
        self.assertEqual(migrated["transcript"], original["transcript"])
        self.assertEqual(migrated["caption_format"], "legacy")
        self.assertEqual(migrated["captions"], "unknown")
        self.assertIsNone(migrated["raw_captions"])
        self.assertTrue((root / "ytmd.pre-v0.2.db").exists())
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertIn("approximate", y.markdown(migrated))
        found = self.cli("search", "invalidation", "--json")
        self.assertEqual(found.returncode, 0)
        self.assertEqual(json.loads(found.stdout)[0]["caption_format"], "legacy")
        self.assertEqual(self.db().execute("SELECT count(*) FROM videos").fetchone()[0], 1)

    def test_newer_schema_rejected(self):
        conn = self.db()
        conn.execute("PRAGMA user_version=99")
        conn.close()
        with self.assertRaises(y.Error):
            y.connect()

    def test_v1_library_gains_chapters_from_description(self):
        root = y.library()
        root.mkdir()
        old = sqlite3.connect(root / "ytmd.db")
        old.executescript("""CREATE TABLE videos (
            id TEXT PRIMARY KEY, title TEXT, channel TEXT, url TEXT, uploaded_at TEXT, duration_s INTEGER,
            description TEXT, captions TEXT, lang TEXT, ingested_at TEXT, transcript TEXT,
            cues_json TEXT, raw_captions TEXT, caption_format TEXT);
            CREATE TABLE passages (id INTEGER PRIMARY KEY, video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE, start REAL NOT NULL, end REAL NOT NULL, text TEXT NOT NULL);
            CREATE INDEX passages_video ON passages(video_id,start);
            CREATE VIRTUAL TABLE passages_fts USING fts5(text, content='passages', content_rowid='id', tokenize='unicode61');
            CREATE TRIGGER passages_ai AFTER INSERT ON passages BEGIN INSERT INTO passages_fts(rowid,text) VALUES(new.id,new.text); END;
            CREATE TRIGGER passages_ad AFTER DELETE ON passages BEGIN INSERT INTO passages_fts(passages_fts,rowid,text) VALUES('delete',old.id,old.text); END;
            PRAGMA user_version=1;""")
        old.execute("INSERT INTO videos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (KEY, "A tutorial", "Test", y.url_for(KEY), "2026-01-01", 130, "Chapters:\n00:00 — Intro\n01:00 — Cache\n", "manual", "en", "2026-09-07T00:00:00Z", "[0:00] Use List<T>.", json.dumps([dict(start=0, end=4, text="Use List<T>.")]), "raw", "json3"))
        old.execute("INSERT INTO passages(video_id,start,end,text) VALUES (?,?,?,?)", (KEY, 0, 4, "Use List<T>."))
        old.commit()
        old.close()
        conn = self.db()
        migrated = dict(conn.execute("SELECT chapters_json, cues_json, caption_format FROM videos").fetchone())
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual([c["title"] for c in json.loads(migrated["chapters_json"])], ["Intro", "Cache"])
        self.assertEqual(migrated["caption_format"], "json3")
        self.assertIn("List<T>", migrated["cues_json"])

    def test_search_returns_multiple_timestamped_passages(self):
        self.seed()
        p = self.cli("search", "cache invalidation", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(len(data), 2)
        self.assertEqual({r["start"] for r in data}, {60, 120})
        self.assertIn("&t=", data[0]["url"])
        self.assertEqual(data[0]["captions"], "manual")
        self.assertEqual(data[0]["caption_format"], "json3")

    def test_update_and_delete_fts(self):
        conn = self.seed()
        changed = row([dict(start=10, end=20, text="Entirely new material")])
        y.save(conn, changed)
        self.assertEqual(json.loads(self.cli("search", "cache", "--json").stdout), [])
        self.assertEqual(len(json.loads(self.cli("search", "material", "--json").stdout)), 1)
        self.assertEqual(self.cli("rm", KEY, "--json").returncode, 0)
        self.assertEqual(json.loads(self.cli("search", "material", "--json").stdout), [])

    def test_show_time_window(self):
        self.seed()
        p = self.cli("show", KEY, "--from", "0:50", "--to", "1:10", "--json")
        data = json.loads(p.stdout)
        self.assertEqual(len(data["passages"]), 1)
        self.assertEqual(data["passages"][0]["start"], 60)
        p = self.cli("show", KEY, "--from", "2:00", "--to", "1:00", "--json")
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stderr)["error"]["code"], "invalid_range")

    def test_failed_update_rolls_back_video_and_search(self):
        conn = self.seed()
        with self.assertRaises(ValueError):
            y.save(conn, dict(row(), title="Must roll back", cues_json="not json"))
        self.assertEqual(conn.execute("SELECT title FROM videos").fetchone()[0], "A tutorial")
        self.assertEqual(len(json.loads(self.cli("search", "cache", "--json").stdout)), 2)

    def test_show_boundary(self):
        self.seed()
        data = json.loads(self.cli("show", KEY, "--from", "65", "--to", "120", "--json").stdout)
        self.assertEqual(data["passages"], [])

    def test_existing_ingestion_idempotent_and_repairs_markdown(self):
        self.seed()
        with patch.object(y, "fetch", side_effect=AssertionError("network called")), redirect_stdout(io.StringIO()):
            self.assertEqual(y.main([KEY, "--json"]), 0)
        self.assertTrue((y.library() / f"{KEY}.md").exists())
        p = self.cli(KEY, "--json")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout)["status"], "existing")

    def test_atomic_export_keeps_previous_file_on_failure(self):
        self.seed()
        path = Path(y.write_markdown(row()))
        before = path.read_text()
        with patch.object(y.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                y.write_markdown(dict(row(), title="changed"))
        self.assertEqual(path.read_text(), before)
        self.assertEqual(list(y.library().glob(".ytmd-*")), [])

    def test_export_stable_filename_removes_old_slug_after_success(self):
        self.seed()
        old = y.library() / f"{KEY}-old-title.md"
        old.write_text("legacy")
        p = self.cli("export", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(old.exists())
        self.assertIn("List&lt;T&gt;", (y.library() / f"{KEY}.md").read_text())

    def test_json_errors_no_tracebacks(self):
        for args in [("search", "test", "-n", "nope"), ("search", "test", "-n", "-1"), ("add", "url", "--lang", "all"), ("add",), ("get", "url", "extra"), ("show", KEY, "--from", "nan"), ("show", KEY, "--to"), ("list", "--force")]:
            p = self.cli(*args, "--json")
            self.assertEqual(p.returncode, 2, (args, p.stderr))
            self.assertEqual(json.loads(p.stderr)["error"]["code"], "usage")
            self.assertNotIn("Traceback", p.stderr)

    def test_literal_search_handles_punctuation_and_unicode(self):
        conn = self.seed()
        y.save(conn, row([dict(start=0, end=5, text="日本語 中文 café C++ foo-bar")]))
        for query in ("中文", "café", "C++", "foo-bar"):
            p = self.cli("search", query, "--json")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(len(json.loads(p.stdout)), 1, query)

    def test_deletion_requires_exact_id(self):
        self.seed()
        self.assertNotEqual(self.cli("rm", "tutorial").returncode, 0)
        self.assertEqual(len(json.loads(self.cli("list", "--json").stdout)), 1)

    def test_get_cached_plain_is_offline_and_has_no_metadata(self):
        self.seed()
        with patch.object(y, "fetch", side_effect=AssertionError("network called")), redirect_stdout(io.StringIO()) as captured:
            self.assertEqual(y.main(["get", KEY, "--plain", "--from", "0", "--to", "5"]), 0)
        self.assertEqual(captured.getvalue().strip(), "Use List<T> to store data.")
        self.assertEqual(self.cli("show", KEY, "--plain", "--from", "0", "--to", "5").stdout.strip(), "Use List<T> to store data.")

    def test_explicit_language_does_not_silently_use_wrong_cached_track(self):
        self.seed()
        for command in ("add", "get"):
            p = self.cli(command, KEY, "--lang", "de", "--json")
            self.assertEqual(p.returncode, 1)
            self.assertEqual(json.loads(p.stderr)["error"]["code"], "language_mismatch")
        self.assertEqual(self.cli("get", KEY, "--lang", "en", "--json").returncode, 0)

    def test_get_invalid_range_does_not_create_library(self):
        p = self.cli("get", KEY, "--from", "60", "--to", "20", "--json")
        self.assertEqual(json.loads(p.stderr)["error"]["code"], "invalid_range")
        self.assertFalse(y.library().exists())

    def test_new_argument_validation(self):
        for args in [("get", KEY, "--plain"), ("show", KEY, "--plain"), ("search", "test", "--context", "121"), ("search", "test", "--context", "-1"), ("search", "test", "--context", "nope"), ("search", "test", "--match", "semantic"), ("list", "--offset", "-1"), ("list", "--limit", "101")]:
            p = self.cli(*args, "--json")
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertEqual(json.loads(p.stderr)["error"]["code"], "usage")

    def test_add_accepts_multiple_urls_without_fetching(self):
        conn = self.seed()
        extra = dict(row(), id="dQw4w9WgXcQ", title="Another tutorial", channel="Fireship")
        y.save(conn, extra)
        p = self.cli("add", KEY, "dQw4w9WgXcQ", "--json")
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertEqual(len(data), 2)
        self.assertEqual({item["id"] for item in data}, {KEY, "dQw4w9WgXcQ"})
        self.assertTrue(all(item["status"] == "existing" for item in data))

    def test_search_can_filter_by_channel(self):
        conn = self.seed()
        y.save(conn, dict(row(), id="dQw4w9WgXcQ", title="Another tutorial", channel="Fireship", cues_json=json.dumps([dict(start=0, end=4, text="Cache invalidation requires care.")])))
        all_hits = json.loads(self.cli("search", "invalidation", "--json").stdout)
        self.assertGreaterEqual(len(all_hits), 2)
        fireship = json.loads(self.cli("search", "invalidation", "--channel", "Fireship", "--json").stdout)
        self.assertTrue(fireship)
        self.assertTrue(all(hit["video_id"] == "dQw4w9WgXcQ" for hit in fireship))

    def test_search_next_command_reads_a_bounded_window(self):
        conn = self.db()
        y.save(conn, dict(row([
            dict(start=720.25, end=725.75, text="Needle in a long interview"),
            dict(start=1500, end=1505, text="Unrelated later section"),
        ]), duration_s=7200))
        p = self.cli("search", "needle")
        self.assertEqual(p.returncode, 0, p.stderr)
        command = shlex.split(p.stdout.rsplit("Next: ", 1)[1])
        self.assertEqual(command, ["ytmd", "show", KEY, "--from", "12:00", "--to", "14:00"])
        read = self.cli(*command[1:], "--json")
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertEqual([c["text"] for c in json.loads(read.stdout)["passages"]], ["Needle in a long interview"])
        machine = self.cli("search", "needle", "--json")
        self.assertIsInstance(json.loads(machine.stdout), list)
        self.assertNotIn("Next:", machine.stdout)
        self.assertEqual(machine.stderr, "")

    def test_search_next_window_includes_context_and_fractional_end(self):
        conn = self.db()
        y.save(conn, row([
            dict(start=0.25, end=1, text="Opening context"),
            dict(start=100.25, end=101, text="Needle"),
            dict(start=200.25, end=201.75, text="Closing context"),
        ]))
        p = self.cli("search", "needle", "--context", "120")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(f"Next: ytmd show {KEY} --from 0:00 --to 3:22", p.stdout)

    def test_search_next_window_includes_long_matching_cue(self):
        conn = self.db()
        y.save(conn, row([dict(start=0.25, end=180.75, text="Needle")]))
        p = self.cli("search", "needle")
        self.assertIn(f"Next: ytmd show {KEY} --from 0:00 --to 3:01", p.stdout)
        self.assertNotIn("Next:", self.cli("search", "unmatched").stdout)

    def test_search_any_broadens_without_changing_default(self):
        self.seed()
        self.assertEqual(json.loads(self.cli("search", "cache unicorn", "--json").stdout), [])
        data = json.loads(self.cli("search", "cache unicorn", "--match", "any", "--json").stdout)
        self.assertEqual(len(data), 2)
        self.assertNotIn("context", data[0])

    def test_search_context_preserves_match_and_adds_nearby_cues(self):
        conn = self.db()
        y.save(conn, row([dict(start=0, end=5, text="Introduction"), dict(start=10, end=15, text="Cache invalidation"), dict(start=20, end=25, text="A useful conclusion"), dict(start=90, end=95, text="Outside the context window")]))
        p = self.cli("search", "invalidation", "--context", "15", "--video", KEY, "--json")
        data = json.loads(p.stdout)[0]
        self.assertEqual(data["text"], "Cache invalidation")
        self.assertEqual(data["start"], 10)
        context = data["context"]
        self.assertEqual((context["start"], context["end"]), (0, 25))
        self.assertIn("Introduction", context["text"])
        self.assertIn("conclusion", context["text"])
        self.assertNotIn("Outside", context["text"])
        self.assertTrue(context["url"].endswith("&t=0s"))
        self.assertTrue(data["url"].endswith("&t=10s"))

    def test_list_filters_and_pages_stably(self):
        conn = self.seed()
        y.save(conn, dict(row(), id="dQw4w9WgXcQ", title="Another tutorial", channel="Fireship"))
        self.assertEqual(len(json.loads(self.cli("list", "tutorial", "--json").stdout)), 2)
        first = json.loads(self.cli("list", "--limit", "1", "--json").stdout)[0]
        second = json.loads(self.cli("list", "--limit", "1", "--offset", "1", "--json").stdout)[0]
        self.assertNotEqual(first["id"], second["id"])
        filtered = json.loads(self.cli("list", "fireship", "--json").stdout)
        self.assertEqual(len(filtered), 1)
        self.assertIn("path", filtered[0])
        self.assertEqual(json.loads(self.cli("list", "unmatched", "--json").stdout), [])
        self.assertEqual(json.loads(self.cli("list", "%", "--json").stdout), [])
        self.assertEqual(json.loads(self.cli("list", "_", "--json").stdout), [])

    def test_command_specific_help(self):
        p = self.cli("help", "get")
        self.assertEqual(p.returncode, 0)
        self.assertIn("--plain", p.stdout)
        self.assertNotIn("--context", p.stdout)
        info = self.cli("help", "info")
        self.assertEqual(info.returncode, 0)
        self.assertIn("chapters", info.stdout)

    def test_info_returns_chapters_without_transcript(self):
        conn = self.db()
        y.save(conn, dict(row(), chapters_json=json.dumps([dict(start=0, end=60, title="Intro"), dict(start=60, end=130, title="Main")])))
        p = self.cli("info", KEY, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual([c["title"] for c in data["chapters"]], ["Intro", "Main"])
        self.assertTrue(data["chapters"][0]["url"].endswith("&t=0s"))
        self.assertNotIn("passages", data)
        self.assertNotIn("List<T>", p.stdout)
        human = self.cli("info", KEY)
        self.assertIn("Intro", human.stdout)
        self.assertNotIn("Cache invalidation", human.stdout)

    def test_markdown_includes_chapter_table_of_contents(self):
        text = y.markdown(dict(row(), chapters_json=json.dumps([dict(start=0, end=60, title="Intro"), dict(start=60, end=130, title="Main")])))
        self.assertIn("## Chapters", text)
        self.assertIn("Intro", text)
        self.assertLess(text.index("## Chapters"), text.index("## Transcript"))

    def test_search_phrase_requires_adjacent_words(self):
        conn = self.db()
        y.save(conn, row([dict(start=0, end=5, text="the software of moats"), dict(start=10, end=15, text="software moats disappeared")]))
        all_hits = json.loads(self.cli("search", "software", "moats", "--json").stdout)
        self.assertEqual({r["start"] for r in all_hits}, {0, 10})
        phrase = json.loads(self.cli("search", "software", "moats", "--match", "phrase", "--json").stdout)
        self.assertEqual([r["start"] for r in phrase], [10])

    def test_list_includes_dates(self):
        self.seed()
        data = json.loads(self.cli("list", "--json").stdout)[0]
        self.assertEqual(data["uploaded_at"], "2026-01-01")
        self.assertEqual(data["ingested_at"], "2026-09-07T00:00:00Z")

    def test_long_transcript_warns_without_a_window(self):
        conn = self.db()
        y.save(conn, dict(row(), duration_s=1200))
        p = self.cli("show", KEY)
        self.assertIn("ytmd info", p.stderr)
        windowed = self.cli("show", KEY, "--from", "0:00", "--to", "1:00")
        self.assertNotIn("ytmd info", windowed.stderr)
        silent = self.cli("show", KEY, "--json")
        self.assertNotIn("ytmd info", silent.stderr)

    def test_doctor_does_not_create_library(self):
        p = self.cli("doctor", "--json")
        self.assertIn("fts5", json.loads(p.stdout))
        self.assertFalse(y.library().exists())


class IngestIntegration(Isolated):
    def setUp(self):
        super().setUp()
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "yt-dlp"
        stub.write_text("#!" + sys.executable + "\n" + '''import sys, os, json
from pathlib import Path
a=sys.argv[1:]
assert '--ignore-config' in a
assert '--skip-download' in a
key=a[-1].rsplit('v=',1)[-1]
log=os.environ.get('YTMD_TEST_LOG')
if log:
    with open(log, 'a') as f:
        print(key, file=f)
mode=json.loads(os.environ.get('YTMD_TEST_ERRORS','{}')).get(key, os.environ.get('YTMD_TEST_MODE',''))
if mode == 'captionless-json':
    print(json.dumps(dict(id='jNQXAC9IVRw', title='Real video', duration=100, channel='Test', subtitles={}, automatic_captions={})))
    sys.exit(0)
if mode == 'incomplete-json':
    print(json.dumps(dict(id='jNQXAC9IVRw', title='Incomplete metadata', subtitles={}, automatic_captions={})))
    sys.exit(0)
if mode == 'unavailable-json':
    print(json.dumps(dict(id='jNQXAC9IVRw', title='youtube video #jNQXAC9IVRw', duration=None)))
    sys.exit(0)
if mode:
    print(mode,file=sys.stderr)
    sys.exit(1)
if '--dump-single-json' in a:
    print(json.dumps(dict(id=key, title='Fixture', duration=100, chapters=[{'start_time':0,'end_time':100,'title':'The only chapter'}], automatic_captions={'en-orig':[{'ext':'json3'}], 'en-de':[{'ext':'json3'}]})))
else:
    assert a[a.index('--sub-langs')+1] == 'en\\\\-orig'
    assert '--write-auto-subs' in a
    assert '--write-subs' not in a
    path=Path(a[a.index('-o')+1]).parent / 'captions.en-orig.json3'
    path.write_text(json.dumps({'events':[{'tStartMs':60000,'dDurationMs':1000,'segs':[{'utf8':'Store List<T> safely'}]}]}))
''')
        stub.chmod(0o755)
        self.pathenv = patch.dict(os.environ, {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")})
        self.pathenv.start()
        self.addCleanup(self.pathenv.stop)

    def test_batch_cli_returns_partial_results_and_retains_successes(self):
        missing, last = "dQw4w9WgXcQ", "7TKqQ2hyM5k"
        with patch.dict(os.environ, {"YTMD_TEST_ERRORS": json.dumps({missing: "This video is unavailable"})}):
            p = self.cli("add", KEY, missing, last, "--json")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stderr, "")
        data = json.loads(p.stdout)
        self.assertEqual([r["status"] for r in data], ["saved", "error", "saved"])
        self.assertEqual(data[1]["error"]["code"], "video_unavailable")
        self.assertEqual({r["id"] for r in json.loads(self.cli("list", "--json").stdout)}, {KEY, last})
        for result in (data[0], data[2]):
            self.assertTrue(Path(result["path"]).exists())

    def test_batch_cli_stops_requests_on_rate_limit(self):
        limited, last = "dQw4w9WgXcQ", "7TKqQ2hyM5k"
        log = self.root / "requests.log"
        with patch.dict(os.environ, {"YTMD_TEST_ERRORS": json.dumps({limited: "HTTP Error 429: Too Many Requests"}), "YTMD_TEST_LOG": str(log)}):
            p = self.cli("add", KEY, limited, last, "--json")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stderr, "")
        self.assertEqual([r["status"] for r in json.loads(p.stdout)], ["saved", "error", "skipped"])
        self.assertEqual(log.read_text().splitlines(), [KEY, KEY, limited])

    def test_end_to_end_ingest_search_show(self):
        p = self.cli(KEY, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["captions"], "auto")
        self.assertEqual(data["lang"], "en-orig")
        self.assertEqual(data["duration_s"], 100)
        self.assertEqual([c["title"] for c in data["chapters"]], ["The only chapter"])
        self.assertTrue(Path(data["path"]).exists())
        self.assertIn("## Chapters", Path(data["path"]).read_text())
        conn = self.db()
        saved = conn.execute("SELECT * FROM videos").fetchone()
        self.assertIn("List<T>", saved["raw_captions"])
        self.assertIn("List<T>", saved["transcript"])
        self.assertEqual(len(json.loads(self.cli("search", "safely", "--json").stdout)), 1)
        self.assertEqual(len(json.loads(self.cli("show", KEY, "--from", "59", "--to", "62", "--json").stdout)["passages"]), 1)

    def test_get_saves_then_returns_one_structured_transcript(self):
        p = self.cli("get", KEY, "--from", "59", "--to", "62", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["status"], "saved")
        self.assertEqual(data["passages"][0]["text"], "Store List<T> safely")
        self.assertEqual([c["title"] for c in data["chapters"]], ["The only chapter"])
        self.assertTrue(Path(data["path"]).exists())
        self.assertEqual(p.stderr, "")
        with patch.dict(os.environ, {"YTMD_TEST_MODE": "network must not be called"}):
            second = self.cli("get", KEY, "--lang", "en", "--json")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["status"], "existing")

    def test_get_plain_can_be_piped_without_status_lines(self):
        p = self.cli("get", KEY, "--plain")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "Store List<T> safely")

    def test_rate_limit_preserves_existing_record(self):
        conn = self.db()
        y.save(conn, row())
        with patch.dict(os.environ, {"YTMD_TEST_MODE": "HTTP Error 429: Too Many Requests"}):
            p = self.cli(KEY, "--force", "--json")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stderr)["error"]["code"], "rate_limited")
        self.assertEqual(conn.execute("SELECT title FROM videos").fetchone()[0], "A tutorial")

    def test_auth_failure_never_automatically_reads_cookies(self):
        with patch.dict(os.environ, {"YTMD_TEST_MODE": "Sign in to confirm your age"}):
            p = self.cli(KEY, "--json")
        self.assertEqual(json.loads(p.stderr)["error"]["code"], "authentication_required")

    def test_missing_captions_are_not_reported_as_a_gone_video(self):
        for mode in ("captionless-json", "incomplete-json"):
            with self.subTest(mode=mode), patch.dict(os.environ, {"YTMD_TEST_MODE": mode}):
                p = self.cli(KEY, "--json")
                self.assertEqual(p.returncode, 1)
                self.assertEqual(p.stdout, "")
                self.assertEqual(json.loads(p.stderr)["error"]["code"], "captions_unavailable")
                self.assertFalse((y.library() / f"{KEY}.md").exists())

    def test_gone_video_is_not_reported_as_caption_less(self):
        with patch.dict(os.environ, {"YTMD_TEST_MODE": "unavailable-json"}):
            dumped = self.cli(KEY, "--json")
        self.assertEqual(dumped.returncode, 1)
        self.assertEqual(json.loads(dumped.stderr)["error"]["code"], "video_unavailable")
        with patch.dict(os.environ, {"YTMD_TEST_MODE": "ERROR: [youtube] jNQXAC9IVRw: This video is unavailable"}):
            failed = self.cli(KEY, "--json")
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stderr)["error"]["code"], "video_unavailable")


class Installer(Isolated):
    def setUp(self):
        super().setUp()
        self.home = self.root / "home"
        self.home.mkdir()
        binary = self.root / "bin"
        binary.mkdir()
        fake = binary / "yt-dlp"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o755)
        fake_curl = binary / "curl"
        fake_curl.write_text("#!" + sys.executable + "\nimport sys,shutil,os\nfrom pathlib import Path\na=sys.argv[1:]\nurl=a[a.index('-o')-1]\nshutil.copyfile(Path(os.environ['FAKE_RELEASE'])/url.split('/')[-1],a[a.index('-o')+1])\n")
        fake_curl.chmod(0o755)
        self.release = self.root / "release"
        self.release.mkdir()
        for name in ("ytmd", "SKILL.md", "LICENSE"):
            (self.release / name).write_bytes((ROOT / name).read_bytes())
        (self.release / "SHA256SUMS").write_text("\n".join(hashlib.sha256((self.release / name).read_bytes()).hexdigest() + "  " + name for name in ("ytmd", "SKILL.md", "LICENSE")))
        self.install_env = patch.dict(os.environ, {"HOME": str(self.home), "PATH": str(binary) + os.pathsep + os.environ.get("PATH", ""), "FAKE_RELEASE": str(self.release)})
        self.install_env.start()
        self.addCleanup(self.install_env.stop)

    def install(self, *args):
        return subprocess.run(["sh", str(ROOT / "install.sh"), *args], capture_output=True, text=True)

    def test_local_install_and_update_all_agents(self):
        for _ in range(2):
            p = self.install("--source", str(ROOT), "--agent", "all")
            self.assertEqual(p.returncode, 0, p.stderr)
        cli = self.home / ".local/bin/ytmd"
        self.assertTrue(cli.is_symlink())
        self.assertTrue((self.home / ".agents/skills/ytmd/SKILL.md").exists())
        self.assertTrue((self.home / ".claude/skills/ytmd/SKILL.md").exists())
        result = subprocess.run([str(cli), "--version"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(y.VERSION, result.stdout)
        help_text = subprocess.run([str(cli), "help"], capture_output=True, text=True).stdout
        for name in ("map", "bundle", "verify", "import"):
            self.assertIn(name, help_text)
        self.assertFalse(y.library().exists())

    def test_remote_install_verifies_payload(self):
        p = self.install("--agent", "none")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((self.home / ".local/bin/ytmd").exists())
        self.assertFalse((self.home / ".agents").exists())

    def test_bad_checksum_leaves_install_untouched(self):
        (self.release / "ytmd").write_text("tampered content")
        p = self.install()
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Checksum mismatch", p.stderr)
        self.assertFalse((self.home / ".local/bin/ytmd").exists())

    def test_refuse_unmanaged_binary(self):
        cli = self.home / ".local/bin/ytmd"
        cli.parent.mkdir(parents=True)
        cli.write_text("keep me")
        p = self.install("--source", str(ROOT))
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(cli.read_text(), "keep me")

    def test_invalid_agent(self):
        self.assertEqual(self.install("--agent", "unknown").returncode, 2)


if __name__ == "__main__":
    unittest.main()
