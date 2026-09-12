"""Mechanical source-text verification for saved bundles."""
import json

from test_map import VideoMap
from test_ytmd import KEY, row, y

SECOND = "dQw4w9WgXcQ"


class VerifyBehavior(VideoMap):
    def bundle(self, *videos, query="cache"):
        data = self.data("bundle", *videos, "--query", query, "--context", "0")
        path = self.root / "research.evidence.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return data, path

    def test_correct_quotes_pass(self):
        self.save(KEY)
        data, path = self.bundle(KEY)
        quote = data["evidence"][0]["text"]
        claims = self.root / "quotes.json"
        claims.write_text(json.dumps(dict(schema_version=1, quotes=[dict(evidence_id=data["evidence"][0]["id"], quote=quote)])))
        result = self.data("verify", str(path), "--claims", str(claims))
        self.assertTrue(result["ok"])
        self.assertEqual(result["quotes"]["failures"], [])

    def test_fabricated_quote_with_valid_timestamp_fails(self):
        self.save(KEY)
        data, path = self.bundle(KEY)
        claims = self.root / "quotes.json"
        claims.write_text(json.dumps(dict(schema_version=1, quotes=[dict(evidence_id=data["evidence"][0]["id"], quote="This sentence is not in the captions.")])))
        code, out, err = self.call("verify", str(path), "--claims", str(claims))
        self.assertEqual(code, 1)
        result = json.loads(out)
        self.assertFalse(result["ok"])
        self.assertEqual(result["quotes"]["failures"][0]["code"], "quote_not_in_evidence")

    def test_quote_from_another_item_fails(self):
        self.save(KEY, cues=[dict(start=0, end=2, text="first cache"), dict(start=60, end=62, text="second cache")])
        data, path = self.bundle(KEY)
        self.assertGreaterEqual(len(data["evidence"]), 2)
        claims = self.root / "quotes.json"
        claims.write_text(json.dumps(dict(schema_version=1, quotes=[dict(evidence_id=data["evidence"][0]["id"], quote=data["evidence"][1]["text"])])))
        result = json.loads(self.call("verify", str(path), "--claims", str(claims))[1])
        self.assertEqual(result["quotes"]["failures"][0]["code"], "quote_not_in_evidence")

    def test_stale_snapshot_is_reported(self):
        self.save(KEY)
        data, path = self.bundle(KEY)
        y.save(self.db(), dict(row(), title="Replaced title"))
        code, out, err = self.call("verify", str(path))
        self.assertEqual(code, 1)
        result = json.loads(out)
        self.assertEqual(result["library_match"]["failures"][0]["code"], "source_stale")

    def test_missing_source_does_not_fetch(self):
        self.save(KEY)
        data, path = self.bundle(KEY)
        self.assertEqual(self.call("rm", KEY)[0], 0)
        code, out, err = self.call("verify", str(path))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["library_match"]["failures"][0]["code"], "source_missing")

    def test_tampered_excerpt_fails_even_if_digest_is_recomputed(self):
        self.save(KEY)
        data, path = self.bundle(KEY)
        data["evidence"][0]["text"] = "tampered " + data["evidence"][0]["text"]
        data["evidence"][0]["ref"]["digest"] = y.sha256_text(data["evidence"][0]["text"])
        path.write_text(json.dumps(data))
        result = json.loads(self.call("verify", str(path))[1])
        self.assertEqual(result["library_match"]["failures"][0]["code"], "excerpt_mismatch")

    def test_unicode_offsets_round_trip(self):
        self.save(KEY, cues=[dict(start=0, end=4, text="Cache café 日本語")])
        data, path = self.bundle(KEY, query="café")
        item = data["evidence"][0]
        self.assertIn("café", item["text"])
        claims = self.root / "quotes.json"
        claims.write_text(json.dumps(dict(schema_version=1, quotes=[dict(evidence_id=item["id"], quote="café")])))
        self.assertTrue(self.data("verify", str(path), "--claims", str(claims))["ok"])
