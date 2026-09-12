# Website development

Static HTML/CSS/JS in `site/`; GitHub Pages deploys from `main`. No build step,
model endpoint, or analytics. The CLI release remains v0.5.0.

## Keep it simple

The user rejected the multi-panel source review as messy and noisy. The page now
shows one use case: give an existing agent a video and a task, then get practical
next steps with timestamps. One example and one setup button; sources and setup
instructions expand on demand. Terminal commands and complete examples live in
the linked documentation, not another landing-page section.

The demo is authored synthetic material. Keep its label, exact quotes, and caption
requirement. Do not replace it with private library content or fake live processing.
`PRODUCT.md`, `DESIGN.md`, and the surface brief record the intent outside `site/`.

## Checks

```bash
python3 -m unittest discover -s tests -q
node --check site/app.js
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

Optional browser suite, using already-installed tools (no automatic installs):

```bash
YTMD_PLAYWRIGHT_MODULE=/path/to/existing/playwright-core \
YTMD_CHROMIUM=/path/to/existing/chromium \
node tests/browser_site.cjs http://127.0.0.1:8000/
```

Omit overrides when your tooling already resolves Playwright Core and Chromium.
The suite checks 1440/390/320px and a 720px scale-2 layout, source links, keyboard,
copy success/denial, deep links, no-JavaScript access, and a 230-word default-copy
ceiling. It saves desktop/mobile captures under ignored `.impeccable/review/`.
The scale-2 check approximates 200% layout, not browser-chrome zoom automation.

## Share image

`tools/social-card.html` renders `site/assets/social.png` at 1200×630. Replace
`{{BASE}}` with the local site origin. Navigate to that origin before setting the
HTML, then wait for and verify Barlow and Inter fonts. Preserve embedded origin
metadata. Font licenses ship in `site/assets/`.

Use a new cache query for changed web assets. Do not bump the CLI or rewrite release
checksums for website-only work.
