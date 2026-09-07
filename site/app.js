'use strict';

const installCode = document.getElementById('install-code');
const installNote = document.getElementById('install-note');
const macCommands = installCode.textContent;
const linuxCommands = macCommands.replace('brew install python yt-dlp', 'pipx install yt-dlp');
const status = document.getElementById('copy-status');
let statusTimer;

// The full macOS setup remains readable without JavaScript.
document.querySelectorAll('button[hidden]').forEach(button => { button.hidden = false; });

for (const button of document.querySelectorAll('[data-os]')) {
  button.addEventListener('click', () => {
    const isMac = button.dataset.os === 'macos';
    document.querySelectorAll('[data-os]').forEach(item => {
      item.setAttribute('aria-pressed', String(item === button));
    });
    installCode.textContent = isMac ? macCommands : linuxCommands;
    if (isMac) {
      const link = document.createElement('a');
      link.href = 'https://brew.sh/';
      link.textContent = 'Homebrew';
      installNote.replaceChildren('With ', link, ' installed, paste into your terminal:');
    } else {
      installNote.textContent = 'First install Python 3.9+ (with SQLite FTS5) and pipx using your package manager. Then paste:';
    }
  });
}

for (const button of document.querySelectorAll('[data-copy]')) {
  button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copy);
    clearTimeout(statusTimer);
    try {
      await navigator.clipboard.writeText(target.textContent.trim());
      status.textContent = button.dataset.copy === 'install-code' ? 'Install commands copied.' : 'Prompt copied. Paste it into your coding agent.';
    } catch {
      // Clipboard permission can be denied. Select the visible, identical text instead.
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(target);
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Clipboard unavailable. Text selected — press ⌘C or Ctrl+C to copy.';
    }
    statusTimer = setTimeout(() => { status.textContent = ''; }, 6000);
  });
}

for (const link of document.querySelectorAll('.mobile-menu nav a')) {
  link.addEventListener('click', () => {
    document.querySelector('.mobile-menu').open = false;
  });
}
