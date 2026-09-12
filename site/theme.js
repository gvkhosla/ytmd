'use strict';

// Runs before CSS paints. Store only an explicit theme choice, never browsing data.
(() => {
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  let preference = null;
  try {
    const saved = localStorage.getItem('ytmd-theme');
    if (saved === 'light' || saved === 'dark') preference = saved;
  } catch { /* Storage may be blocked; system preference and the toggle still work. */ }

  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#0a0a0a' : '#fafafa';
    const button = document.getElementById('theme-toggle');
    if (button) {
      const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
      button.setAttribute('aria-label', label);
      button.title = label;
      button.hidden = false;
    }
  }

  apply(preference || (media.matches ? 'dark' : 'light'));
  media.addEventListener('change', event => {
    if (!preference) apply(event.matches ? 'dark' : 'light');
  });
  document.addEventListener('DOMContentLoaded', () => {
    apply(document.documentElement.dataset.theme);
    document.getElementById('theme-toggle').addEventListener('click', () => {
      preference = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(preference);
      try { localStorage.setItem('ytmd-theme', preference); } catch { /* Session-only choice. */ }
    });
  });
})();
