"""Stable evidence references survive reindexing and bind to snapshots."""
import json

from test_map import VideoMap
from test_ytmd import KEY, y


class EvidenceRefs(VideoMap):
    def test_read_and_context_include_additive_refs(self):
        self.save(KEY, chapters=[dict(start=0, end=60, title="Introduction"), dict(start=60, end=130, title="Technique")])
        read = self.data("read", KEY, "--chapter", "2")
        self.assertTrue(all("ref" in p and "id" in p for p in read["passages"]))
        self.assertEqual(read["passages"][0]["ref"]["video_id"], KEY)
        self.assertEqual(read["passages"][0]["ref"]["source_snapshot"], read["source_snapshot"])
        context = self.data("context", KEY, "--query", "cache")
        self.assertTrue(all("ref" in p for p in context["evidence"]))

    def test_refs_survive_markdown_export_and_fts_rebuild(self):
        self.save(KEY)
        bundle = self.data("bundle", KEY, "--query", "cache", "--context", "0")
        refs = [item["ref"] for item in bundle["evidence"]]
        self.data("export")
        with y.connect() as conn:
            conn.execute("DELETE FROM passages_fts")
            conn.execute("INSERT INTO passages_fts(rowid, text) SELECT id, text FROM passages")
            conn.commit()
        later = self.data("bundle", KEY, "--query", "cache", "--context", "0")
        self.assertEqual([item["ref"]["passage_index"] for item in later["evidence"]], [r["passage_index"] for r in refs])
        self.assertEqual([item["ref"]["passage_digest"] for item in later["evidence"]], [r["passage_digest"] for r in refs])
        path = self.root / "bundle.json"
        path.write_text(json.dumps(bundle))
        self.assertTrue(self.data("verify", str(path))["ok"])
