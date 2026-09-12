---
name: ytmd
description: One video, one task, a plan with timestamps.
colors:
  paper: "#fafafa"
  ink: "#111111"
  muted: "#3f3f46"
  green: "#047857"
  green-hover: "#065f46"
  line: "rgb(17 17 17 / 10%)"
  selected: "#d1fae5"
  on-green: "#ffffff"
  overlay: "#111111"
  on-overlay: "#ffffff"
  dark-paper: "#0a0a0a"
  dark-ink: "#fafafa"
  dark-muted: "#a1a1aa"
  dark-green: "#34d399"
  dark-green-hover: "#6ee7b7"
  dark-line: "rgb(250 250 250 / 12%)"
  dark-selected: "#064e3b"
  dark-on-green: "#052e16"
typography:
  display:
    fontFamily: "'Barlow Semi Condensed', sans-serif"
    fontSize: "clamp(3.25rem, 7vw, 5rem)"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.03em"
  intro:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "20px"
    lineHeight: 1.65
  body:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "16px"
    lineHeight: 1.65
  group:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 600
  task:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
  task-mobile:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
  label:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "14px"
rounded:
  citation: "3px"
  control: "4px"
  media: "min(1vw, 12px)"
spacing:
  compact: "12px"
  group: "20px"
  wide: "28px"
  section: "48px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.on-green}"
    rounded: "{rounded.control}"
    padding: "12px 16px"
    height: "48px"
  citation:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.green}"
    rounded: "{rounded.citation}"
    padding: "0 6px"
---

# Design System: ytmd

## Overview

**Creative North Star: "One line, then proof"**

The page is high-contrast and short. A stacked hero states the offer; six real videos prove it; local Markdown and SQLite are explained after. Barlow Semi Condensed and Inter stay. The previous cool-gray navy identity is retired.

## Colors

Near-white paper, true black ink, and emerald for the single primary action, timestamps, and focus. Headings stay ink in both themes so color is not doing hierarchy twice. No large colored marketing panels.

Dark mode is near-black paper, pale ink, zinc muted text, and mint buttons with dark green type. Thumbnail overlays stay black/white. The wordmark has a dedicated dark SVG. Photographs are never inverted. Text/action pairs meet 4.5:1.

## Typography

Barlow Semi Condensed is the display face, Inter the reading face, with OpenType features enabled. Monospace is only for timestamps and durations. Body is 16px. The intro is 20px. Group titles 24px; tasks 18px (20px on mobile). Result text is ink, not muted.

## Layout

1080px maximum, 24px gutters (20px below 600px). The hero is a left-aligned stack: headline, one sentence, one button. Galleries are three / two / one columns. Mechanism steps are a three-column description list after the videos. No cards, tabs, or sidebars.

## Elevation & Depth

Flat. Opacity-based hairlines. Copy feedback floats in light mode only; dark mode uses no shadow.

## Shapes

4px controls. Thumbnails use `min(1vw, 12px)` radius and an inset outline. Native disclosure markers.

## Components

### Setup action

One emerald button copies the setup prompt. Failure opens and selects the instructions. Theme toggle is not a second primary.

### Source citations

YouTube timestamp links sit with short exact quotes. Coverage and caption provenance stay in the disclosure.

### Theme utility

Follows system until the user chooses. Dedicated light/dark wordmarks. No CSS filters on rasters.

## Do's and Don'ts

- **Do** pair each video with one task and one short result.
- **Do** keep exact quotes and limitations available.
- **Do** make the next action singular.
- **Don't** restore mid-tone gray type, a two-column essay hero, or extra marketing sections.
- **Don't** invert photographs or the logo with filters.
