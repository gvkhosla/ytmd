# Changelog

## 0.4.8

- Search with context merges overlapping or touching windows from the same video. Keep the best hit's fields unchanged and include all selected citations in `matches` for merged groups; repeated speech is preserved.
- Add `search --diverse` to select hits round-robin across videos in best-hit order. Relevance ranking remains the default; video/channel filters still apply.
- `-n` limits selected matches before merging, so output can contain fewer windows. Search without context keeps the individual-hit shape.

## 0.4.7

- `doctor` reports the resolved running CLI path and ytmd installations in PATH order, warning about distinct installations.
- Report yt-dlp version/release age using a bounded local version command; warn after 90 days or when the age cannot be determined.
- Warnings are advisory: no network health checks, automatic updates, PATH edits, or changes to the library. Existing required-dependency exit behavior is unchanged.

## 0.4.6

- Batch `add` reports every input in order, preserving successful saves when another video fails. JSON returns an array with per-input errors and exits 1 on any failure; single-video behavior is unchanged.
- Stop batch processing after a rate limit or interruption and mark remaining inputs as skipped, without further requests.
- Human output streams successes to stdout and failures/skips to stderr.

## 0.4.5

- Do not classify missing metadata or placeholder-like titles alone as unavailable videos; allow live and caption-bearing metadata through.
- Search suggests a bounded `show --from … --to …` window, including the top hit and requested context. JSON output is unchanged.

## 0.4.4

- Classify deleted and missing videos as `video_unavailable` instead of `captions_unavailable`.

## 0.4.3

- `ytmd search` prints `Next: ytmd show ID --from MM:SS` so a hit becomes a read.

## 0.4.2

- `ytmd list` shows caption language next to duration (`en · 12:04`).

## 0.4.1

- `ytmd add URL [URL ...]` saves several videos in one command. Single-URL `--json` shape is unchanged.
- `ytmd search --channel NAME` restricts hits to that exact channel.

## 0.4.0

- `info VIDEO`: metadata and chapter outline without dumping the transcript.
- Parse chapters from YouTube/yt-dlp metadata or description timestamps; include them in add/get/show JSON and markdown.
- `search --match phrase`: require query words to appear adjacently.
- `list --json` includes `uploaded_at` and `ingested_at`; add/get JSON includes `duration_s`.
- Warn before printing a long transcript without a time window.
- Existing libraries gain chapters from saved descriptions (schema 2).

## 0.3.0

- `get URL`: save once and read in one command, with time-window and JSON support.
- `get/show --plain`: clean transcript text for copying or piping.
- `search --context SECONDS`: surrounding captions, with original match fields preserved.
- `search --match any`: broader keyword retrieval without embeddings.
- Filter saved videos by title/channel/ID and paginate with `list --limit --offset`.
- Explicit language mismatch errors for cached tracks; per-command `help`.
- Shorter, task-oriented site with copyable commands and static macOS/Linux instructions.
- Plain-text `llms.txt` for agents, linked from the site and agent skill.
- No database migration or added runtime dependencies from v0.2.

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
