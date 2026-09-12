# Website development

The site is static HTML/CSS/JavaScript under `site/`. GitHub Pages deploys from `main`.
There is no build step, model endpoint, analytics integration, or dependency installation.
`PRODUCT.md`, `DESIGN.md`, and `.impeccable/surfaces/site-index-html.md` record the approved
product, visual system, and homepage direction; none are served as part of the site.

## Check locally

```bash
python3 -m unittest discover -s tests -q
node --check site/app.js
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

The optional browser suite uses an **already-installed** Node, Playwright Core, and Chromium:

```bash
YTMD_PLAYWRIGHT_MODULE=/path/to/existing/playwright-core \
YTMD_CHROMIUM=/path/to/existing/chromium \
node tests/browser_site.cjs http://127.0.0.1:8000/
```

If your tooling already resolves `playwright-core` and its Chromium, omit those overrides.
The script never installs them. Browser tooling is optional development infrastructure,
not a dependency of the CLI or deployed page. Screenshots go to the ignored
`.impeccable/review/` directory.

Checks cover 1440, 1280, 720, 390, and 320 CSS-pixel widths; the 720px viewport uses scale 2
as a 200%-equivalent layout check, not browser-chrome zoom automation. They exercise task
switching, each citation, keyboard navigation, responsive DOM order/focus preservation,
copying all eight targets, clipboard denial, deep links, reduced motion, expanded disclosures,
and no-JavaScript access. Python tests separately compare every quote against the fixture
and verify installer commands, metadata, anchors, and assets.

## Demonstration truth

The source review uses exact quotations from `evals/cases.json` and authored responses,
not real video claims or scored agent output. Keep both labels visible. Source links target
local passages, not fictional YouTube IDs. Adding real video evidence requires a source the
user is permitted to publish; do not copy the private local library into the site.

## Sharing image

`tools/social-card.html` is the authored source for `site/assets/social.png` (1200×630).
Replace `{{BASE}}` with the local site origin when rendering. Navigate the browser to that
origin **before** setting the card HTML so fonts load same-origin; a base tag alone does
not change an about:blank document's origin. Wait for fonts, verify Barlow and Inter are
loaded, and capture at 1200×630. Preserve the PNG's embedded origin metadata after rendering.
Font licenses and the existing wordmark live in `site/assets/`.

The website redesign does not change the v0.5.0 CLI release or installer checksums. Use a
new cache query for changed CSS, JavaScript, and social imagery; keep installer and release
links pinned to the actual CLI version.
