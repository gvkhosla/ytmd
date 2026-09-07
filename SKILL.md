---
name: ytmd
description: Ingest a YouTube video into a local transcript library and search it. Use when the user pastes a YouTube URL, wants a video transcript, or wants to apply knowledge from a YouTube video in the current repo.
license: MIT
compatibility: Requires ytmd and yt-dlp on PATH, Python 3.9+.
---

# ytmd

Local YouTube transcripts. Captions only — never download the video.

## Commands

```bash
ytmd "https://www.youtube.com/watch?v=VIDEO_ID"   # ingest
ytmd search "query"
ytmd show VIDEO_ID
ytmd list
ytmd path
```

Library: `~/ytmd/*.md` and `~/ytmd/ytmd.db` (override with `YTMD_DIR`).

## Workflow

1. If `ytmd` is missing, stop and give the install snippet from the README. Do not write a replacement scraper.
2. Ingest the URL. If it says `already ingested`, continue with that id.
3. `ytmd search` for the relevant bits. Do **not** dump a long transcript into context.
4. `ytmd show ID` or read `~/ytmd/ID-*.md` only for the sections you need.
5. Cite `video_id` + timestamp (`[m:ss]`) when applying the knowledge.

## Rules

- Prefer search over reading the whole file.
- On caption 429 / auth errors, retry with `--cookies-from-browser chrome`.
- No playlists, no Whisper. One video URL at a time.
