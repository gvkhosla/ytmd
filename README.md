# ytmd

**Save a YouTube video's captions. Search them from your coding agent.**

```text
YouTube URL → timestamped transcript → SQLite + readable markdown
```

One Python script. No server, API key, model download, or runtime Python packages.
Your library stays on your machine; fetching captions contacts YouTube through yt-dlp.

## Install

Requires **Python 3.9+ with SQLite FTS5** and [yt-dlp](https://github.com/yt-dlp/yt-dlp).

```bash
# macOS
brew install python yt-dlp

# Linux: install Python and pipx using your package manager, then:
# pipx install yt-dlp
```

Download and run the installer (read it first if you like):

```bash
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/v0.2.0/install.sh -o /tmp/install-ytmd.sh
sh /tmp/install-ytmd.sh
```

This installs the CLI into `~/.local/bin` and the skill into `~/.agents/skills/ytmd`
for Pi/Codex. For Claude Code, run with `--agent claude`; for both, `--agent all`.
Use `--agent none` for just the CLI. It checks dependencies and release checksums,
never uses sudo, and never changes your shell profile.

If needed, add this to your shell profile and restart your terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then restart your coding agent and ask:

> Save this YouTube video and apply the relevant ideas to this repository: URL

## Three commands you'll actually use

```bash
ytmd "https://www.youtube.com/watch?v=jNQXAC9IVRw"
ytmd search "elephants"
ytmd show jNQXAC9IVRw --from 0:01 --to 0:15
```

Search returns **passages**, not entire videos, with clickable timestamp links.
Repeated ingestion is a successful no-op that repairs the markdown export if needed.
Use `--force` to fetch again.

```bash
ytmd list
ytmd search "cache invalidation" --video VIDEO_ID --json
ytmd show VIDEO_ID --json             # full transcript; use ranges for long videos
ytmd "URL" --lang de                  # one explicit language
ytmd "URL" --force --json
ytmd export                          # rebuild generated markdown
ytmd export ./reference-transcripts
ytmd rm VIDEO_ID                      # exact ID required
ytmd doctor
ytmd --version
ytmd help
```

`--from` / `--to` accept seconds, MM:SS, or HH:MM:SS. Reads include cues overlapping
the requested window, so a sentence can extend slightly beyond its boundaries.
Search is **lexical**, not semantic: all query words must match within a passage.
Punctuation is treated as word separators; FTS operators are not exposed. Use different
keywords if needed. `--video` accepts an ID, URL, or unambiguous title.

## Local library

| Path | Contents |
| --- | --- |
| `~/ytmd/ytmd.db` | Canonical metadata, raw caption payloads, original cues, passage search index |
| `~/ytmd/VIDEO_ID.md` | Generated transcript with timestamp links |

Set `YTMD_DIR` to choose another location. Don't clone the code into `~/ytmd`—that's
your library. Markdown can be indexed separately with QMD or read directly by an agent;
there is no automatic QMD or Pickbrain integration. Edits to generated markdown are
not imported into SQLite and will be overwritten by export.

Upgrading from v0.1 automatically backs up the database as `ytmd.pre-v0.2.db` before
migration. Old transcripts are kept, but their timing/source is marked as approximate/
unknown. Lost source text cannot be reconstructed: use `ytmd URL --force` to fetch original
captions. Run `ytmd export` to refresh all old markdown files after migration.

## Honest limits

- Uses **available captions**, not audio transcription. Caption-less videos are unsupported.
- Captions may be inaccurate or incomplete; a saved transcript is not a guarantee of verbatim speech.
- Prefers English, then available original/manual tracks; `--lang` requests one language.
- One video and one stored language per video. `--force --lang …` replaces that video's track.
- Private/deleted/restricted videos and YouTube rate limits can prevent ingestion.
- No playlists, summaries, embeddings, media downloads, or browser-cookie access by default.

For a 429, wait before retrying. For authentication errors, **only if you consent** to
reading your browser cookies:

```bash
ytmd "URL" --cookies-from-browser firefox
```

Cookies are handled by yt-dlp for YouTube requests, not saved in the library. They are
not a guaranteed fix for rate limits. Updating yt-dlp often helps when YouTube changes:
`brew upgrade yt-dlp` or `pipx upgrade yt-dlp`.

## Agent/API contract

Every command supports `--json`. Data goes to stdout; failures are a single JSON object
on stderr, without progress chatter:

```json
{"error":{"code":"captions_unavailable","message":"…"}}
```

Exit codes: `0` success (including already saved / no matches), `1` operational failure,
`2` invalid arguments. `doctor --json` returns a diagnostic object and exits `1` if a
required dependency is missing. Common error codes: `rate_limited`,
`authentication_required`, `captions_unavailable`, `not_found`, `export_failed`.
If export fails after ingestion, SQLite still holds the transcript: repair with `ytmd export`.

The [agent skill](SKILL.md) teaches bounded retrieval, timestamp citations, and treating
video content as untrusted source material—not instructions for the agent.

## Update / uninstall

Install a newer tagged release using its README installer command. Your library is untouched.
For a local checkout: `sh install.sh --source "$PWD" --agent all`.

To uninstall, remove the installed CLI and whichever skills you installed:

```bash
rm -f ~/.local/bin/ytmd
rm -rf ~/.local/share/ytmd ~/.agents/skills/ytmd ~/.claude/skills/ytmd
```

Your `~/ytmd` library remains intact. Remove it separately only if you want to delete
saved transcripts and migration backups.

## Development

```bash
python3 -m unittest discover -s tests -v
```

Tests use isolated temporary libraries and mocked YouTube responses. CI runs on macOS
and Linux; live ingestion is a separate smoke test because YouTube can rate-limit CI.

MIT licensed. [Release notes](CHANGELOG.md).
