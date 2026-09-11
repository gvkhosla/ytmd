# ytmd

**YouTube transcripts, ready for your agent.**

Save a video's captions as local markdown. Search timestamped passages from Pi,
Codex, Claude Code, or your terminal. One Python script, SQLite, and yt-dlp.
No API keys, model downloads, or server. Videos need available captions.

[Website](https://gvkhosla.github.io/ytmd/) · [Plain-text agent guide](https://gvkhosla.github.io/ytmd/llms.txt) · [Release](https://github.com/gvkhosla/ytmd/releases/tag/v0.4.4)

## Install

### Ask your coding agent

Copy this prompt:

```text
Install ytmd using https://gvkhosla.github.io/ytmd/llms.txt. Read the instructions
and installer first. Check dependencies, ask before making system changes, and
install the CLI and skill for my agent. Verify with ytmd doctor.
```

### Or use your terminal

**macOS** — requires [Homebrew](https://brew.sh/):

```bash
brew install python yt-dlp
export PATH="$HOME/.local/bin:$PATH"
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/v0.4.4/install.sh -o /tmp/install-ytmd.sh
sh /tmp/install-ytmd.sh --agent all
ytmd doctor
```

**Linux** — first install Python 3.9+ with SQLite FTS5 and pipx using your package manager:

```bash
pipx install yt-dlp
export PATH="$HOME/.local/bin:$PATH"
curl -fsSL https://raw.githubusercontent.com/gvkhosla/ytmd/v0.4.4/install.sh -o /tmp/install-ytmd.sh
sh /tmp/install-ytmd.sh --agent all
ytmd doctor
```

[Read the installer](https://github.com/gvkhosla/ytmd/blob/v0.4.4/install.sh) before running it.
It verifies release checksums, installs into `~/.local/bin`, and adds skills for
Pi/Codex (`~/.agents/skills/ytmd`) and Claude Code (`~/.claude/skills/ytmd`).
Use `--agent pi`, `codex`, `claude`, or `none` instead of `all` to narrow installation.
No sudo or shell-profile changes by the installer. The export above affects the current
terminal; add it to your shell profile if `~/.local/bin` isn't already on PATH.

## Use from your agent

Restart the agent to discover the skill. Paste this prompt and replace the URL:

```text
Save this YouTube video with ytmd. Find the passages relevant to this repository,
cite their timestamps, and suggest how to apply them: [paste URL]
```

The agent retrieves relevant passages instead of automatically dumping the full
transcript into context. It should ask before accessing cookies or making system changes.

## Commands

Try a real video:

```bash
ytmd get "https://youtu.be/DHjqpvDnNGE"
ytmd info DHjqpvDnNGE
ytmd search "javascript" --context 15 -n 3
ytmd show DHjqpvDnNGE --from 0:25 --to 0:45
```

| Command | What it does |
| --- | --- |
| `ytmd add "URL"` (or `ytmd "URL"`) | Save captions and return the file path |
| `ytmd get "URL"` | Save if needed, then print the transcript |
| `ytmd get "URL" --plain` | Text only, without timestamps or metadata; suitable for piping |
| `ytmd info ID` | Metadata and chapter outline, without the transcript |
| `ytmd search "words" --video ID --json` | Find matching passages in one video |
| `ytmd search "words" --match any --context 15` | Match any word and include nearby captions |
| `ytmd search "words" --match phrase` | Require the words to appear next to each other |
| `ytmd show ID --from 12:00 --to 15:00` | Read a time window from a saved video |
| `ytmd list "title or channel" --limit 20 --offset 0` | Filter and paginate saved videos |
| `ytmd export [directory]` | Rebuild markdown from SQLite |
| `ytmd rm VIDEO_ID` | Delete a saved video; exact ID required |
| `ytmd doctor` / `ytmd path` / `ytmd --version` | Inspect setup, library path, or version |
| `ytmd help search` | Read per-command help |

**Reads:** get/show print the full transcript unless a time range is supplied. Both
accept `--plain` or `--json` (mutually exclusive). Times accept seconds, MM:SS, or HH:MM:SS.
Whole cues overlapping a window are included, so a sentence may extend beyond its boundaries.

**Search:** lexical, not semantic. All words must match within a passage by default;
`--match any` broadens this, `--match phrase` requires them in order. Punctuation separates words; FTS operators aren't exposed.
`--context 0–120` adds that many seconds around each hit. Nearby hits may have overlapping
context. `-n` limits results (default 10, max 100). `--video` accepts an ID, URL, or unambiguous title.

**List:** optional literal substring filter on title, channel, or ID. Default limit 50,
max 100. Use `--offset` for subsequent pages. JSON includes local markdown paths, `uploaded_at`, and `ingested_at`.

**Info:** returns title, channel, duration, caption provenance, and chapters when YouTube or the
description provides them. add/get JSON also includes `duration_s` and `chapters`. For long videos,
prefer `info` plus a time window over dumping the full transcript.

**Saving:** repeated ingestion reuses the saved track without fetching YouTube again.
`--lang de` requests one language; `--force` replaces a saved track. If a saved language
differs from an explicit --lang, ytmd reports `language_mismatch` rather than silently
returning the wrong language. Only one track is stored per video.

## For agents and scripts

[llms.txt](site/llms.txt) describes setup, workflow, command outputs, failures, and safety
in plain text. [SKILL.md](SKILL.md) is the installable agent skill.

All data commands support `--json`: one JSON value on stdout, no progress chatter.
Errors go to stderr:

```json
{"error":{"code":"captions_unavailable","message":"..."}}
```

Exit 0 = success (including existing/no matches), 1 = operational failure, 2 = invalid
arguments. `doctor --json` returns diagnostics with `ok: false` and exits 1 when a
required dependency is missing. Help and version output are plain text.

Search results include the matching passage's `video_id`, `title`, `start`, `end`,
`text`, `url`, caption provenance, and score. `--context` adds a separate
`context: {start, end, text, url}` object without changing the matching passage fields.
get/show return metadata, `chapters`, and `passages: [{start, end, text, url}]`; get adds `status`.
`info` returns the same metadata and `chapters` without passages.

## Storage and limits

- `~/ytmd/ytmd.db`: canonical raw captions, cues, metadata, and passage search index.
- `~/ytmd/VIDEO_ID.md`: generated markdown with timestamp links. Edits are overwritten on export.
- Set `YTMD_DIR` to change the library location. Don't clone the source repo into `~/ytmd`.
- Markdown may be indexed separately by QMD. No automatic QMD/Pickbrain integration.
- Captions may be incomplete or inaccurate. No audio transcription, playlists, summaries,
  embeddings, paid API, or media download. Caption-less videos are unsupported.
- Fetching contacts YouTube. Saved content works offline. Restrictions and rate limits still apply.
- For a 429, wait before retrying. Cookies are not a guaranteed fix. For authentication,
  only with explicit consent: `ytmd "URL" --cookies-from-browser BROWSER`.
- If export fails after ingestion, SQLite retains the transcript. Repair with `ytmd export`.

v0.4 adds a `chapters_json` column (schema 2) and backfills it from saved descriptions.
v0.3 libraries open and migrate in place. v0.1 libraries are backed up as
`ytmd.pre-v0.2.db` before migration. Imported timing is approximate and provenance is
unknown; lost text can't be reconstructed. Re-ingest with `--force` to fetch source captions.

## Update / uninstall

To update, run the installer from the new release. Your library is preserved.
Update yt-dlp separately when YouTube changes: `brew upgrade yt-dlp` or `pipx upgrade yt-dlp`.

To uninstall the CLI and installed skills, leaving your transcript library intact:

```bash
rm -f ~/.local/bin/ytmd
rm -rf ~/.local/share/ytmd ~/.agents/skills/ytmd ~/.claude/skills/ytmd
```

## Development

```bash
python3 -m unittest discover -s tests -v
sh install.sh --source "$PWD" --agent all
python3 -m http.server 8000 --directory site
```

Tests use temporary libraries and mocked YouTube responses. CI runs on macOS/Linux.
The website is static HTML/CSS/JS, with self-hosted assets and no analytics or build step.
`site/llms.txt` and all install instructions are available without JavaScript.
GitHub Pages automatically deploys site changes on `main` to https://gvkhosla.github.io/ytmd/.

MIT licensed. [Release notes](CHANGELOG.md).
