# Website development

Static HTML/CSS/JS in `site/`; GitHub Pages deploys from `main`. No runtime build,
model endpoint, analytics, or third-party asset requests. CLI remains v0.5.0.

## Current brief

Keep the established cool paper, navy, green, Barlow, and Inter identity. The user
replaced the single synthetic demo with six real videos and explicitly requested
visual thumbnails plus a simple explanation of local Markdown, SQLite, and search.

- Six locally served thumbnails, three technical / three business.
- One task and short useful result per video. Native disclosures hold adapted
  next steps, short exact quotes, YouTube timestamps, and coverage qualifications.
- One setup-copy button in the hero, plus a separate header theme utility.
  Instructions remain available without JS. Thumbnails appear before the mechanism
  outline so the first mobile viewport includes a real video.
- Three short mechanism steps: save once, search locally, read what matters.
  Storage/retrieval are local; the existing agent’s model may run elsewhere.
- No fake live responses, transcript sidebar, tabs, URL input, or inline command tour.

`examples/videos.json` is the curated source for the static examples block. All six
videos were fetched into an isolated ignored research library with ytmd v0.5.0.
Titles and quoted substrings were checked against returned captions. The private
user library was untouched. Do not commit full transcripts or the research DB.
Automatic captions can contain errors; plans are adaptations, not endorsements,
measured agent outcomes, or full-video reviews. No popularity counts are advertised.

The synthetic retrieval-evaluation fixture remains in `evals/`; it is not website
proof. Existing synthetic workflow documentation remains explicitly labelled.

## Dark mode

`theme.js` runs before CSS to apply a saved `ytmd-theme` choice or the system preference.
The header button switches themes and saves only that explicit preference locally.
System changes apply until a manual override. Blocked storage falls back to an
in-session toggle. Without JS, CSS follows the system and hides the inert button.
Semantic tokens cover text, actions, citations, feedback, and overlays; photographs
are never inverted. The wordmark has a monochrome reversed dark treatment.

## Updating examples

Edit `examples/videos.json` only after retrieving and reading the relevant source.
Keep quotes short and exact; preserve source timestamps, limitations, and provenance.

```bash
python3 tools/render_examples.py --write
python3 tools/render_examples.py --check
```

This is an authoring helper, not a deployment build step. Commit the generated
HTML alongside the manifest. Thumbnail provenance lives in `site/assets/videos/README.md`
and each JPEG’s embedded metadata.

## Checks

```bash
python3 -m unittest discover -s tests -q
node --check site/app.js
node --check site/theme.js
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

Optional browser suite, using already-installed tools (never installs dependencies):

```bash
YTMD_PLAYWRIGHT_MODULE=/path/to/existing/playwright-core \
YTMD_CHROMIUM=/path/to/existing/chromium \
node tests/browser_site.cjs http://127.0.0.1:8000/
```

Checks 1440/390/320px and a 720px scale-2 layout; six thumbnails/plans, exact citation
URLs, keyboard, copy success/denial, deep links, no-JS access, zero external resource
requests, overflow, system/saved theme selection, storage denial, both themes’ AA
text/action contrast, and a 400-word default-copy ceiling. The previous 230-word ceiling
was for one demo; the new cap accommodates the user-requested six without a copy wall.
Screenshots go under ignored `.impeccable/review/`. Scale-2 approximates 200% layout,
not actual browser-chrome zoom.

## Share image

`tools/social-card.html` renders `site/assets/social.png` at 1200×630. Replace `{{BASE}}`
with the local site origin. Navigate there before setting HTML; wait for images and
verify Barlow/Inter fonts. Embed source provenance in the resulting PNG. Font licenses
ship in `site/assets/`; thumbnail rights remain with their owners.

Use new asset cache queries. Do not bump the CLI or rewrite release checksums for
website-only work.
