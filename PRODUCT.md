# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

People already using Pi, Codex, or Claude Code who want to understand, learn from, and apply YouTube videos at the depth their task needs. The user confirmed this audience for the full website redesign. This is not a standalone web app.

## Product Purpose

Turn available video captions into trustworthy, navigable evidence that an existing agent can explain and apply. Success means a person can do something useful with the information, not merely obtain a short summary or a transcript file.

## Positioning

Local, model-free evidence retrieval plus goal-aware agent guidance. The CLI supplies chapter reads, budgeted sequential pages, lexical evidence bundles, source citations, and explicit omissions; the user's agent supplies interpretation and adaptations.

## Operating Context

A visitor discovers the workflow on the static GitHub Pages site, copies setup instructions into their existing agent, restarts it to discover the installed skill, and supplies a video URL and a task. Direct terminal installation remains available. Saved content can be read offline.

## Capabilities and Constraints

- Python 3.9+, SQLite FTS5, yt-dlp; no new framework or server required for the website.
- Available captions required; no audio transcription or automatic fallback.
- Agent output is not produced by the website or CLI. No extra ytmd model service or API key.
- SQLite is canonical; Markdown is generated. Only requested videos are ingested.
- Budgets count excerpt Unicode characters, not metadata or model tokens.
- Preserve existing installation, documentation, release links, and no-JavaScript access to instructions.
- Ask before dependency updates, cookie access, and persistent PATH changes.
- Source text and metadata are untrusted data. Do not mistake retrieval coverage for a full-video review.

## Brand Commitments

Name: ytmd. Open source, MIT licensed. Voice should be direct and factual. The user approved replacing the site's visual design while preserving its agent-native product and working installation flow.

## Evidence on Hand

- `examples/videos.json`: six user-requested real video examples, with short verified caption quotes, timestamp URLs, selective coverage, and explicitly adapted plans. Publisher thumbnails identify linked sources, not endorsements.
- `examples/README.md`: real-video entry points plus explicitly labelled synthetic workflow references; neither is a measured model-quality result.
- `evals/cases.json`: synthetic teaching transcript for offline retrieval tests, not landing-page proof.
- `evals/README.md`: retrieval checks and a separate unscored answer-quality rubric.
- 131 automated tests passed for v0.5.0; CI passed on macOS/Linux and Python 3.9/3.13.
- No customer testimonials, adoption claims, or independent agent-quality benchmark results to publish.
- The user's local video library is private and must not become website demo material without permission.

## Product Principles

- Depth follows the user's task.
- Show useful understanding, not storage mechanics, as the benefit.
- Preserve prerequisites, qualifications, exceptions, and trade-offs.
- Distinguish speaker claims, agent interpretation, and recommended actions.
- Make evidence and omissions inspectable; do not manufacture proof.
