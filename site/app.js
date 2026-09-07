'use strict';

// Content is static HTML. JavaScript only adds clipboard convenience.
const status = document.getElementById('copy-status');
let statusTimer;

for (const button of document.querySelectorAll('[data-copy]')) {
  button.hidden = false;
  button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copy);
    clearTimeout(statusTimer);
    try {
      await navigator.clipboard.writeText(target.textContent.trim());
      status.textContent = button.dataset.message || 'Copied.';
    } catch {
      const range = document.createRange();
      range.selectNodeContents(target);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Clipboard unavailable. Text selected — press ⌘C or Ctrl+C to copy.';
    }
    statusTimer = setTimeout(() => { status.textContent = ''; }, 6000);
  });
}

for (const link of document.querySelectorAll('.mobile-menu nav a')) {
  link.addEventListener('click', () => { document.querySelector('.mobile-menu').open = false; });
}
