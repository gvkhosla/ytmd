# ytmd

YouTube URL in. Full transcript on your machine.

Search it. Read it. Hand it to a coding agent.

No account, no cloud, no Whisper. `yt-dlp` pulls the captions; `ytmd` stores them as markdown + a SQLite FTS5 index in `~/ytmd`.

## Install

```bash
brew install yt-dlp
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/main/ytmd -o ~/.local/bin/ytmd
chmod +x ~/.local/bin/ytmd
```

`~/.local/bin` needs to be on your `PATH`.

## Use

```bash
ytmd "https://www.youtube.com/watch?v=VIDEO_ID"
ytmd search "the thing they said"
ytmd show VIDEO_ID
ytmd list
```

## Coding agent

```bash
mkdir -p ~/.agents/skills/ytmd
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/main/SKILL.md -o ~/.agents/skills/ytmd/SKILL.md
```

Then paste a YouTube URL and say **ingest this**.

Pi loads `~/.agents/skills/` automatically. For Claude Code, use `~/.claude/skills/ytmd/SKILL.md`. Same file.

## Library

| Path | What |
| --- | --- |
| `~/ytmd/*.md` | one markdown file per video |
| `~/ytmd/ytmd.db` | SQLite FTS5 index |

Override with `YTMD_DIR`. Do not clone this repo into `~/ytmd` — that folder is your library.

## Requirements

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

If YouTube rate-limits captions:

```bash
ytmd "URL" --cookies-from-browser chrome
```
