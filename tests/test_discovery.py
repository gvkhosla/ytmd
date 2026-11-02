"""Synthetic catalog fixtures; all network requests mocked."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from unittest.mock import patch
from test_ytmd import Isolated, KEY, row, y

SECOND = "abcdefghijk"
THIRD = "12345678901"


def record(key=KEY, score=10, **kwargs):
    return dict(vid=key, score=score, hn={"recommenders": 3}, title="Synthetic talk",
                channel="Fixture", summary="Catalog overview", why_hn="Repeated recommendations",
                primary_topic="Software design", shelf_life="evergreen", **kwargs)


class Discovery(Isolated):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = y.main([*args, "--json"])
        return code, json.loads(out.getvalue() or err.getvalue())

    def catalog(self, records=None):
        return y.parse_hackertube("\n".join(json.dumps(r) for r in (records or [record()])).encode())

    def test_rank_filter_cache_and_no_transcript_fetch(self):
        news = record(THIRD, 100); news["shelf_life"] = "news"
        with patch.object(y, "fetch_hackertube", return_value=self.catalog([record(), record(SECOND, 20), news])) as fetch, patch.object(y, "fetch") as captions:
            code, data = self.run_cli("discover", "--unseen")
            self.assertEqual(code, 0)
            self.assertEqual([v["id"] for v in data["videos"]], [SECOND, KEY])
            self.assertIn("attribution", data)
            self.assertEqual(self.run_cli("discover")[1]["fetched_at"], data["fetched_at"])
            fetch.assert_called_once()
            captions.assert_not_called()

    def test_unrecommended_and_topic_filter(self):
        other = record(SECOND); other["hn"]["recommenders"] = 0
        with patch.object(y, "fetch_hackertube", return_value=self.catalog([record(), other])):
            self.assertEqual(len(self.run_cli("discover", "--topic", "SOFTWARE")[1]["videos"]), 1)
            self.assertEqual(self.run_cli("discover", "--topic", "unmatched")[1]["videos"], [])

    def test_saved_is_not_delivered_and_record_is_idempotent(self):
        with self.db() as conn:
            y.save(conn, row())
        with patch.object(y, "fetch_hackertube", return_value=self.catalog()):
            self.assertEqual(len(self.run_cli("discover", "--unseen")[1]["videos"]), 1)
        path = self.root / "today.md"
        path.write_text("# Daily digest\nAn agent-written overview.")
        code, data = self.run_cli("digest", str(path), "--videos", KEY)
        self.assertEqual(code, 0)
        self.assertEqual(data["status"], "recorded")
        self.assertEqual(self.run_cli("digest", str(path), "--videos", KEY)[1]["status"], "existing")
        self.assertEqual(self.run_cli("discover", "--unseen")[1]["videos"], [])
        self.assertEqual(len(self.run_cli("discover")[1]["videos"]), 1)
        self.assertEqual(self.db().execute("SELECT COUNT(*) FROM videos").fetchone()[0], 1)

    def test_failed_refresh_preserves_cache(self):
        with patch.object(y, "fetch_hackertube", return_value=self.catalog()):
            self.run_cli("discover")
        with patch.object(y, "fetch_hackertube", side_effect=y.Error("invalid_catalog", "bad")):
            self.assertEqual(self.run_cli("discover", "--refresh")[0], 1)
        self.assertEqual(len(self.run_cli("discover")[1]["videos"]), 1)

    def test_invalid_records(self):
        invalid = [[], {}, record(score=float("nan")), record(score=True), record("bad"), record(score=-1)]
        wrong = record(); wrong["hn"] = None; invalid.append(wrong)
        wrong = record(); wrong["summary"] = []; invalid.append(wrong)
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(y.Error) as exc:
                y.parse_hackertube(json.dumps(value).encode())
            self.assertEqual(exc.exception.code, "invalid_catalog")
        for raw in (b"", b"\xff", b"not json", b'{}\n{}'):
            with self.assertRaises(y.Error):
                y.parse_hackertube(raw)
        with self.assertRaises(y.Error):
            self.catalog([record(), record()])

    def test_download_bounded_and_timeout(self):
        from urllib.error import URLError
        with patch.object(y, "urlopen", side_effect=URLError("offline")) as fetch:
            self.assertEqual(self.run_cli("discover")[1]["error"]["code"], "discovery_unavailable")
            self.assertEqual(fetch.call_args.kwargs["timeout"], 30)
        with patch.object(y, "MAX_CATALOG_BYTES", 1), self.assertRaises(y.Error):
            y.parse_hackertube(b"{}")

    def test_canonical_urls(self):
        data = self.catalog([record(url="https://evil.invalid")])[0]
        self.assertEqual(data["url"], y.url_for(KEY))

    def test_digest_failure_does_not_mark_anything(self):
        self.assertEqual(self.run_cli("digest", str(self.root / "absent.md"), "--videos", KEY)[0], 1)
        path = self.root / "empty.md"; path.write_text("")
        self.assertEqual(self.run_cli("digest", str(path), "--videos", KEY)[0], 1)
        path.write_text("Digest")
        self.assertEqual(self.run_cli("digest", str(path), "--videos", "invalid")[0], 1)
        with patch.object(y, "fetch_hackertube", return_value=self.catalog()):
            self.assertEqual(len(self.run_cli("discover", "--unseen")[1]["videos"]), 1)

    def test_digest_conflicts_preserve_original(self):
        path = self.root / "today.md"; path.write_text("Original")
        self.run_cli("digest", str(path), "--videos", KEY)
        self.assertEqual(self.run_cli("digest", str(path), "--videos", SECOND)[1]["error"]["code"], "digest_conflict")
        path.write_text("Edited")
        self.assertEqual(self.run_cli("digest", str(path), "--videos", KEY)[1]["error"]["code"], "digest_conflict")
        ids = [r[0] for r in self.db().execute("SELECT video_id FROM digest_videos")]
        self.assertEqual(ids, [KEY])

    def test_limit_and_source_validation(self):
        for args in [("--limit", "0"), ("--limit", "26"), ("--source", "unknown")]:
            self.assertEqual(self.run_cli("discover", *args)[0], 2)
