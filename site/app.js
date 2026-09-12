'use strict';

// The full example and instructions are static HTML. No model or network calls.
const copyStatus = document.getElementById('copy-status');
let statusTimer;

for (const button of document.querySelectorAll('[data-copy]')) {
  const target = document.getElementById(button.dataset.copy);
  if (!target) continue;
  button.hidden = false;
  button.addEventListener('click', async () => {
    clearTimeout(statusTimer);
    button.disabled = true;
    try {
      await navigator.clipboard.writeText(target.textContent.trim());
      copyStatus.textContent = button.dataset.message || 'Copied.';
    } catch {
      const selection = window.getSelection();
      if (selection) {
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        copyStatus.textContent = 'Clipboard unavailable. Text selected; press ⌘C or Ctrl+C to copy.';
      } else {
        copyStatus.textContent = 'Clipboard unavailable. Select the instructions and copy them manually.';
      }
    } finally {
      button.disabled = false;
    }
    statusTimer = setTimeout(() => { copyStatus.textContent = ''; }, 6000);
  });
}

const mobileMenu = document.querySelector('.mobile-menu');
for (const link of document.querySelectorAll('.mobile-menu nav a')) {
  link.addEventListener('click', () => { mobileMenu.open = false; });
}

const review = document.getElementById('use');
const tabs = [...document.querySelectorAll('[data-mode]')];
const answers = [...document.querySelectorAll('.answer')];
const passages = [...document.querySelectorAll('.source-passage')];
const sourceScroll = document.getElementById('source-passages');
const sourceCount = document.getElementById('source-count');
const demoStatus = document.getElementById('demo-status');
const citations = [...document.querySelectorAll('.citation')];
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function selectMode(mode, announce = true) {
  const activeAnswer = document.getElementById(`answer-${mode}`);
  if (!activeAnswer) return;
  const sources = new Set(activeAnswer.dataset.sources.split(' '));
  for (const tab of tabs) {
    const selected = tab.dataset.mode === mode;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  }
  for (const answer of answers) answer.hidden = answer !== activeAnswer;
  for (const passage of passages) {
    passage.hidden = !sources.has(passage.id);
    passage.classList.remove('is-selected');
  }
  for (const citation of citations) citation.removeAttribute('aria-current');
  sourceScroll.scrollTop = 0;
  sourceCount.textContent = `${sources.size} of ${passages.length} passages`;
  if (announce) {
    demoStatus.textContent = `${mode[0].toUpperCase() + mode.slice(1)} example. Showing ${sources.size} of ${passages.length} synthetic source passages.`;
    if (location.hash.startsWith('#source-')) {
      history.replaceState(null, '', location.pathname + location.search + '#use');
    }
  }
}

function selectSource(id, moveFocus = true) {
  const target = passages.find(passage => passage.id === id);
  if (!target) return;
  if (target.hidden) {
    const answer = answers.find(panel => panel.dataset.sources.split(' ').includes(id));
    if (!answer) return;
    selectMode(answer.id.replace('answer-', ''), false);
  }
  for (const passage of passages) passage.classList.toggle('is-selected', passage === target);
  for (const citation of citations) {
    if (citation.hash === `#${id}` && !citation.closest('.answer').hidden) {
      citation.setAttribute('aria-current', 'true');
    } else {
      citation.removeAttribute('aria-current');
    }
  }
  sourceScroll.scrollTo({ top: target.offsetTop, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  if (moveFocus) {
    // On narrow screens the source follows the answer, so bring the source into view too.
    sourceScroll.scrollIntoView({ block: 'nearest', behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    target.focus({ preventScroll: true });
    demoStatus.textContent = `Source passage at ${target.querySelector('.source-time').firstChild.textContent.trim()} selected.`;
  }
}

for (const answer of answers) {
  answer.setAttribute('role', 'tabpanel');
  answer.setAttribute('aria-labelledby', answer.id.replace('answer-', 'tab-'));
}
for (const [index, tab] of tabs.entries()) {
  tab.addEventListener('click', () => selectMode(tab.dataset.mode));
  tab.addEventListener('keydown', event => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    tabs[next].focus();
    selectMode(tabs[next].dataset.mode);
  });
}
for (const citation of citations) {
  citation.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    selectSource(citation.hash.slice(1));
    history.replaceState(null, '', citation.hash);
  });
}

// Keep the keyboard/screen-reader sequence aligned with the responsive visual order.
const reviewGrid = document.querySelector('.review-grid');
const sourceColumn = document.querySelector('.source-column');
const narrowReview = window.matchMedia('(max-width: 800px)');
function arrangeReviewColumns() {
  const focused = document.activeElement;
  const restoreFocus = sourceColumn.contains(focused);
  if (narrowReview.matches) reviewGrid.append(sourceColumn);
  else reviewGrid.prepend(sourceColumn);
  if (restoreFocus) focused.focus({ preventScroll: true });
}
arrangeReviewColumns();
narrowReview.addEventListener('change', arrangeReviewColumns);

selectMode('apply', false);
review.classList.add('is-enhanced');
document.getElementById('demo-controls').hidden = false;
if (location.hash.startsWith('#source-')) selectSource(location.hash.slice(1));
window.addEventListener('hashchange', () => {
  if (location.hash.startsWith('#source-')) selectSource(location.hash.slice(1));
});
