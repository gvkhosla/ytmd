'use strict';

// Static example and instructions. JavaScript only reveals citations and helps copy text.
function reveal(target) {
  for (let details = target.closest('details'); details; details = details.parentElement.closest('details')) {
    details.open = true;
  }
}

for (const link of document.querySelectorAll('.citation')) {
  link.addEventListener('click', () => {
    const target = document.getElementById(link.hash.slice(1));
    if (target) reveal(target);
    // Keep native fragment navigation, focus, and browser history.
  });
}
function revealFragment() {
  const target = document.getElementById(location.hash.slice(1));
  if (!target) return;
  reveal(target);
  if (target.matches('.sources article')) target.focus();
}
revealFragment();
window.addEventListener('hashchange', revealFragment);

const status = document.getElementById('copy-status');
let timer;
for (const button of document.querySelectorAll('[data-copy]')) {
  const target = document.getElementById(button.dataset.copy);
  if (!target) continue;
  button.hidden = false;
  button.addEventListener('click', async () => {
    clearTimeout(timer);
    button.disabled = true;
    try {
      await navigator.clipboard.writeText(target.textContent.trim());
      status.textContent = 'Copied. Paste into your agent to set up ytmd.';
    } catch {
      reveal(target);
      const selection = window.getSelection();
      if (selection) {
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        target.scrollIntoView({ block: 'nearest' });
        status.textContent = 'Text selected. Press ⌘C or Ctrl+C to copy.';
      } else {
        status.textContent = 'Copy unavailable. Select the setup instructions and copy them manually.';
      }
    } finally {
      button.disabled = false;
    }
    timer = setTimeout(() => { status.textContent = ''; }, 6000);
  });
}
