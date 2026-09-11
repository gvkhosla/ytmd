#!/bin/sh
# Install a pinned release. No sudo, shell-profile edits, cookies, or model downloads.
set -eu
VERSION=0.4.4
AGENT=shared
SOURCE=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --agent) [ "$#" -ge 2 ] || { echo 'Missing --agent value' >&2; exit 2; }; AGENT=$2; shift 2 ;;
        --source) [ "$#" -ge 2 ] || { echo 'Missing --source directory' >&2; exit 2; }; SOURCE=$2; shift 2 ;;
        -h|--help) echo 'Usage: sh install.sh [--agent shared|pi|codex|claude|all|none] [--source LOCAL_REPO]'; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
case "$AGENT" in shared|pi|codex|claude|all|none) ;; *) echo 'Unknown agent' >&2; exit 2 ;; esac
command -v python3 >/dev/null 2>&1 || { echo 'Install Python 3.9+ first.' >&2; exit 1; }
command -v yt-dlp >/dev/null 2>&1 || {
    echo 'Install yt-dlp first: brew install yt-dlp (macOS) or pipx install yt-dlp (Linux).' >&2
    exit 1
}
python3 -c 'import sys,sqlite3; assert sys.version_info >= (3,9), "Python 3.9+ required"; sqlite3.connect(":memory:").execute("CREATE VIRTUAL TABLE t USING fts5(x)")'
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT HUP INT TERM
if [ -n "$SOURCE" ]; then
    for file in ytmd SKILL.md LICENSE; do cp "$SOURCE/$file" "$WORK/$file"; done
else
    command -v curl >/dev/null 2>&1 || { echo 'Install curl first.' >&2; exit 1; }
    BASE="https://raw.githubusercontent.com/gvkhosla/ytmd/v$VERSION"
    for file in ytmd SKILL.md LICENSE SHA256SUMS; do
        curl --proto '=https' --tlsv1.2 -fsSL "$BASE/$file" -o "$WORK/$file"
    done
    python3 - "$WORK" <<'PY'
import hashlib, pathlib, sys
root = pathlib.Path(sys.argv[1])
expected = dict((line.split()[1], line.split()[0]) for line in (root / 'SHA256SUMS').read_text().splitlines())
for name in ('ytmd', 'SKILL.md', 'LICENSE'):
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if expected.get(name) != actual:
        sys.exit('Checksum mismatch: ' + name)
PY
fi
# Test the candidate before changing the current installation.
python3 "$WORK/ytmd" doctor --json >/dev/null
BIN="$HOME/.local/bin"
DEST="$HOME/.local/share/ytmd"
mkdir -p "$BIN" "$DEST"
if [ -e "$BIN/ytmd" ] || [ -L "$BIN/ytmd" ]; then
    if [ "$(readlink "$BIN/ytmd" 2>/dev/null || true)" != "$DEST/ytmd" ]; then
        echo "Refusing to replace an unmanaged $BIN/ytmd. Move it aside after reviewing it, then retry." >&2
        exit 1
    fi
fi
for file in ytmd SKILL.md LICENSE; do
    cp "$WORK/$file" "$DEST/.$file.new"
    if [ "$file" = ytmd ]; then chmod 755 "$DEST/.$file.new"; else chmod 644 "$DEST/.$file.new"; fi
    mv -f "$DEST/.$file.new" "$DEST/$file"
done
ln -sfn "$DEST/ytmd" "$BIN/ytmd"
install_skill() {
    mkdir -p "$1/ytmd"
    cp "$WORK/SKILL.md" "$1/ytmd/.SKILL.md.new"
    mv -f "$1/ytmd/.SKILL.md.new" "$1/ytmd/SKILL.md"
}
case "$AGENT" in
    shared|pi|codex) install_skill "$HOME/.agents/skills" ;;
    claude) install_skill "$HOME/.claude/skills" ;;
    all) install_skill "$HOME/.agents/skills"; install_skill "$HOME/.claude/skills" ;;
esac
printf 'Installed ytmd %s → %s\n' "$VERSION" "$BIN/ytmd"
case ":$PATH:" in
    *":$BIN:"*) ;;
    *) printf '\nAdd this to your shell profile, then restart your terminal:\n  export PATH="$HOME/.local/bin:$PATH"\n' ;;
esac
printf '\nRestart your coding agent to discover the skill. Then ask: “Save this YouTube video and find the relevant passages: URL”\n'
