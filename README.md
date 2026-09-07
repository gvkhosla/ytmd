# ytmd

**Watch it once. Build with it.**

Turn YouTube captions into local, searchable transcripts your coding agent can use.

**[Website & quick start](https://gvkhosla.github.io/ytmd/)** · [Latest release](https://github.com/gvkhosla/ytmd/releases/latest) · [Agent skill](SKILL.md)

```text
YouTube URL → timestamped transcript → SQLite + readable markdown
```

One Python script. No server, API key, model download, or runtime Python packages.
Your library stays on your machine; fetching captions contacts YouTube through yt-dlp.
Works from **Pi, Codex, Claude Code, or your terminal**. Videos need available captions.

## Let your coding agent set it up

Paste this into your coding agent:

```text
Install ytmd from https://github.com/gvkhosla/ytmd. Read the README and
installer first, check my dependencies, and ask before making system
changes. Install the CLI and skill for my agent, then verify with ytmd doctor.
```

Or install it yourself below.

## Install

Requires **Python 3.9+ with SQLite FTS5** and [yt-dlp](https://github.com/yt-dlp/yt-dlp).
You can [read the installer](https://github.com/gvkhosla/ytmd/blob/v0.2.0/install.sh) before running it.

### macOS

With [Homebrew](https://brew.sh/) installed:

```bash
brew install python yt-dlp
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/v0.2.0/install.sh -o /tmp/install-ytmd.sh
sh /tmp/install-ytmd.sh --agent all
export PATH="$HOME/.local/bin:$PATH"
ytmd doctor
```

### Linux

First install Python (including SQLite FTS5) and pipx using your distribution's
package manager. Then:

```bash
pipx install yt-dlp
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/v0.2.0/install.sh -o /tmp/install-ytmd.sh
sh /tmp/install-ytmd.sh --agent all
export PATH="$HOME/.local/bin:$PATH"
ytmd doctor
```

These commands install the CLI into `~/.local/bin` and skills for Pi/Codex
(`~/.agents/skills/ytmd`) and Claude Code (`~/.claude/skills/ytmd`).
Use `--agent pi`, `--agent codex`, or `--agent claude` for just your agent,
or `--agent none` for CLI only. The installer checks dependencies and release
checksums, never uses sudo, and never changes your shell profile.

The `export PATH=…` command applies to the current terminal. If `~/.local/bin` isn't
already on your PATH, add that line to your shell profile too.

### Your first video

Restart your coding agent to discover the skill. Then paste a YouTube URL and ask:

> Save this YouTube video and apply the relevant ideas to this repository: URL

The agent can save captions, search relevant passages, and read timestamped windows
instead of loading an entire video into context. It does not automatically summarize
or modify your repository without a task from you.

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

### Landing page

The shareable site is plain HTML/CSS/JS in [`site/`](site/), with self-hosted fonts
and no analytics, third-party scripts, or build step. Preview it locally:

```bash
python3 -m http.server 8000 --directory site
```

Open `http://localhost:8000`. `.github/workflows/pages.yml` publishes `site/` to
[GitHub Pages](https://gvkhosla.github.io/ytmd/) when site files change on `main`.
The CLI stays independently versioned; the website's installer points to the tested
`v0.2.0` release, not an untagged development script.

MIT licensed. [Release notes](CHANGELOG.md).
