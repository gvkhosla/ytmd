"""Batch ingestion contracts; all fetches mocked and libraries temporary."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
from unittest.mock import patch

from test_ytmd import Isolated, KEY, row, y

SECOND = "dQw4w9WgXcQ"
THIRD = "7TKqQ2hyM5k"


class BatchAdd(Isolated):
    def run_add(self, urls, errors=None, flags=None, json_mode=True):
        calls = []

        def fetch(key, language, browser):
            calls.append((key, language, browser))
            if key in (errors or {}):
                raise errors[key]
            return dict(row(), id=key, title=key, url=y.url_for(key))

        out, err = io.StringIO(), io.StringIO()
        with patch.object(y, "fetch", side_effect=fetch), redirect_stdout(out), redirect_stderr(err):
            code = y.main(["add", *urls, *(flags or []), *(["--json"] if json_mode else [])])
        return code, out.getvalue(), err.getvalue(), calls

    def test_partial_failure_reports_ordered_results_and_keeps_saves(self):
        code, out, err, calls = self.run_add([KEY, SECOND, THIRD], {SECOND: y.Error("video_unavailable", "Gone")})
        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual([r["status"] for r in data], ["saved", "error", "saved"])
        self.assertEqual(data[1], {"status": "error", "url": SECOND, "error": {"code": "video_unavailable", "message": "Gone"}})
        self.assertEqual([c[0] for c in calls], [KEY, SECOND, THIRD])
        saved = {r[0] for r in self.db().execute("SELECT id FROM videos")}
        self.assertEqual(saved, {KEY, THIRD})
        for item in (data[0], data[2]):
            self.assertTrue(Path(item["path"]).exists())
        code, out, err, calls = self.run_add([KEY, THIRD])
        self.assertEqual(code, 0)
        self.assertEqual([r["status"] for r in json.loads(out)], ["existing", "existing"])
        self.assertEqual(calls, [])

    def test_all_failures_still_return_an_array(self):
        code, out, err, calls = self.run_add([KEY, SECOND], {
            KEY: y.Error("captions_unavailable", "No captions"),
            SECOND: y.Error("authentication_required", "Needs consent"),
        })
        self.assertEqual(code, 1)
        self.assertEqual([r["status"] for r in json.loads(out)], ["error", "error"])
        self.assertEqual(err, "")
        self.assertTrue(all(c[2] is None for c in calls))

    def test_rate_limit_skips_every_remaining_input_without_fetching(self):
        code, out, err, calls = self.run_add([KEY, SECOND, THIRD, KEY], {SECOND: y.Error("rate_limited", "Wait")})
        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual([r["status"] for r in data], ["saved", "error", "skipped", "skipped"])
        self.assertEqual([r["url"] for r in data[2:]], [THIRD, KEY])
        self.assertEqual(data[2]["error"]["code"], "batch_stopped")
        self.assertIn("rate_limited", data[2]["error"]["message"])
        self.assertEqual([c[0] for c in calls], [KEY, SECOND])

    def test_interrupt_preserves_results_and_stops(self):
        code, out, err, calls = self.run_add([KEY, SECOND, THIRD], {SECOND: KeyboardInterrupt()})
        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual([r["status"] for r in data], ["saved", "error", "skipped"])
        self.assertEqual(data[1]["error"]["code"], "interrupted")
        self.assertEqual(len(calls), 2)

    def test_invalid_url_is_isolated_without_network(self):
        code, out, err, calls = self.run_add(["not a URL", KEY])
        self.assertEqual(code, 1)
        self.assertEqual([r["status"] for r in json.loads(out)], ["error", "saved"])
        self.assertEqual(json.loads(out)[0]["error"]["code"], "invalid_url")
        self.assertEqual([c[0] for c in calls], [KEY])

    def test_duplicate_url_reuses_saved_track(self):
        code, out, err, calls = self.run_add([KEY, y.url_for(KEY)])
        self.assertEqual(code, 0)
        self.assertEqual([r["status"] for r in json.loads(out)], ["saved", "existing"])
        self.assertEqual(len(calls), 1)

    def test_single_url_json_success_and_failure_are_unchanged(self):
        code, out, err, calls = self.run_add([KEY])
        self.assertEqual(code, 0)
        self.assertIsInstance(json.loads(out), dict)
        self.assertEqual(json.loads(out)["status"], "saved")
        code, out, err, calls = self.run_add([SECOND], {SECOND: y.Error("rate_limited", "Wait")})
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(json.loads(err), {"error": {"code": "rate_limited", "message": "Wait"}})

    def test_human_mode_prints_successes_and_errors_on_separate_streams(self):
        code, out, err, calls = self.run_add([KEY, SECOND, THIRD], {SECOND: y.Error("rate_limited", "Wait")}, json_mode=False)
        self.assertEqual(code, 1)
        self.assertIn(f"saved: {KEY}", out)
        self.assertIn("Read: ytmd show", out)
        self.assertNotIn("rate_limited", out)
        self.assertIn(f"error: {SECOND}: rate_limited", err)
        self.assertIn(f"skipped: {THIRD}: batch_stopped", err)

    def test_export_failure_does_not_lose_saved_record_or_hide_next_result(self):
        write_markdown = y.write_markdown

        def fail_once(record):
            if record["id"] == KEY:
                raise OSError("Disk unavailable")
            return write_markdown(record)

        with patch.object(y, "write_markdown", side_effect=fail_once):
            code, out, err, calls = self.run_add([KEY, SECOND])
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(data[0]["error"]["code"], "export_failed")
        self.assertEqual(data[1]["status"], "saved")
        self.assertEqual(self.db().execute("SELECT count(*) FROM videos").fetchone()[0], 2)

    def test_operational_failure_does_not_discard_earlier_results(self):
        for error in (OSError("disk"), sqlite3.OperationalError("locked"), ValueError("bad JSON")):
            with self.subTest(error=error):
                code, out, err, calls = self.run_add([KEY, SECOND], {SECOND: error})
                self.assertEqual(code, 1)
                self.assertIn(json.loads(out)[0]["status"], ("saved", "existing"))
                self.assertEqual(json.loads(out)[1]["error"]["code"], "operation_failed")
                self.assertEqual(err, "")

    def test_force_failure_preserves_existing_track_and_passes_options(self):
        y.save(self.db(), row())
        code, out, err, calls = self.run_add([KEY, SECOND], {KEY: y.Error("rate_limited", "Wait")}, flags=["--force", "--lang", "de", "--cookies-from-browser", "firefox"])
        self.assertEqual(code, 1)
        self.assertEqual(calls, [(KEY, "de", "firefox")])
        self.assertEqual(self.db().execute("SELECT title FROM videos WHERE id=?", (KEY,)).fetchone()[0], "A tutorial")
        self.assertEqual(json.loads(out)[1]["status"], "skipped")
