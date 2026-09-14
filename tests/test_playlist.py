"""Playlist/channel expansion and captions-unavailable next steps."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from unittest.mock import patch

from test_batch import SECOND, THIRD
from test_ytmd import Isolated, KEY, row, y


PLAYLIST = "https://www.youtube.com/playlist?list=PLabcdefghijk"
CHANNEL = "https://www.youtube.com/@Fireship/videos"


class Classify(Isolated):
    def test_watch_url_with_list_stays_a_single_video(self):
        self.assertEqual(y.classify_input(f"https://www.youtube.com/watch?v={KEY}&list=PLabc"), ("video", KEY))

    def test_playlist_and_channel_are_collections(self):
        self.assertEqual(y.classify_input(PLAYLIST)[0], "collection")
        self.assertEqual(y.classify_input(CHANNEL)[0], "collection")
        self.assertEqual(y.classify_input("https://www.youtube.com/channel/UC1234567890")[0], "collection")

    def test_video_id_still_rejects_playlists(self):
        with self.assertRaises(y.Error) as raised:
            y.video_id(PLAYLIST)
        self.assertEqual(raised.exception.code, "invalid_url")
        self.assertIn("playlist", raised.exception.message)


class PlaylistAdd(Isolated):
    def test_playlist_entries_take_limit_and_skip_junk(self):
        payload = json.dumps({
            "_type": "playlist",
            "entries": [{"id": KEY}, {"id": None}, {"id": SECOND}, {"id": KEY}, {"id": THIRD}],
        })
        with patch.object(y, "run_ytdlp", return_value=payload) as run:
            found = y.playlist_entries(PLAYLIST, 2, None)
        self.assertEqual(found, [KEY, SECOND])
        args, kwargs = run.call_args
        self.assertTrue(kwargs.get("allow_playlist"))
        self.assertIn("--playlist-end", args[0])
        self.assertIn("2", args[0])

    def test_add_playlist_expands_then_saves_like_a_batch(self):
        calls = []

        def fetch(key, language, browser):
            calls.append(key)
            return dict(row(), id=key, title=key, url=y.url_for(key))

        out, err = io.StringIO(), io.StringIO()
        with patch.object(y, "playlist_entries", return_value=[KEY, SECOND]), patch.object(y, "fetch", side_effect=fetch), redirect_stdout(out), redirect_stderr(err):
            code = y.main(["add", PLAYLIST, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(err.getvalue(), "")
        data = json.loads(out.getvalue())
        self.assertEqual([item["status"] for item in data], ["saved", "saved"])
        self.assertEqual([item["id"] for item in data], [KEY, SECOND])
        self.assertEqual(calls, [KEY, SECOND])

    def test_add_limit_caps_collection_expansion(self):
        with patch.object(y, "playlist_entries", return_value=[KEY]) as expand, patch.object(y, "fetch", return_value=row()), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = y.main(["add", PLAYLIST, "--limit", "1", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(expand.call_args.args[1], 1)

    def test_empty_playlist_is_a_single_error(self):
        err = io.StringIO()
        with patch.object(y, "playlist_entries", return_value=[]), redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = y.main(["add", PLAYLIST, "--json"])
        self.assertEqual(code, 1)
        data = json.loads(err.getvalue())
        self.assertEqual(data["error"]["code"], "empty_collection")


class CaptionsNext(Isolated):
    def test_captions_unavailable_includes_import_and_cookies_next_steps(self):
        with self.assertRaises(y.Error) as raised:
            y.choose_track(dict(id=KEY, subtitles={}, automatic_captions={}))
        self.assertEqual(raised.exception.code, "captions_unavailable")
        actions = [step["action"] for step in raised.exception.next_steps]
        self.assertEqual(actions, ["import", "cookies"])
        self.assertIn(KEY, raised.exception.next_steps[0]["command"])

    def test_single_video_json_error_envelope_includes_next(self):
        err = io.StringIO()
        with patch.object(y, "fetch", side_effect=y.Error("captions_unavailable", "No captions", next_steps=y.captions_next(KEY))), redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = y.main(["add", KEY, "--json"])
        self.assertEqual(code, 1)
        data = json.loads(err.getvalue())
        self.assertEqual(data["error"]["code"], "captions_unavailable")
        self.assertEqual(data["error"]["next"][0]["action"], "import")
