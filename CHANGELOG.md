# Changelog

## 0.2.0

- Preserve raw caption payloads and original cue timing in SQLite.
- Keep multiline VTT captions, technical angle-bracket notation, and repeated speech.
- Determine manual/automatic provenance from metadata; download exactly one caption track.
- Search timestamped passages; read time windows with `show --from --to`.
- Link results and markdown timestamps directly to YouTube.
- Back up and migrate v0.1 databases; label imported timing/provenance honestly.
- Idempotent ingestion, atomic markdown replacement, and export repair.
- Strict YouTube URL validation, no user yt-dlp config hooks, explicit browser-cookie consent.
- Standard argument parsing, consistent JSON/error output, dependency diagnostics.
- Pinned installer with payload checksums, portable agent skill, offline tests and CI.

## 0.1.0

Initial single-file CLI: captions via yt-dlp, SQLite FTS5, markdown exports, agent skill.
