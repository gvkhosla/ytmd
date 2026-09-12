---
name: ytmd
description: One video, one task, a useful answer with source timestamps.
colors:
  paper: "#f4f6fa"
  ink: "#172638"
  muted: "#526071"
  green: "#195e54"
  green-hover: "#124b43"
  line: "#d7dfe7"
  selected: "#e3eee8"
  on-green: "#ffffff"
  overlay: "#172638"
  on-overlay: "#ffffff"
  dark-paper: "#101820"
  dark-ink: "#e6edf5"
  dark-muted: "#a6b5c5"
  dark-green: "#8ed4bd"
  dark-green-hover: "#b5e6d6"
  dark-line: "#344453"
  dark-selected: "#203b36"
  dark-on-green: "#102820"
typography:
  display:
    fontFamily: "'Barlow Semi Condensed', sans-serif"
    fontSize: "clamp(3.25rem, 6vw, 4.5rem)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  intro:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "17px"
    lineHeight: 1.65
  body:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "16px"
    lineHeight: 1.65
  detail:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "15px"
  label:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "14px"
  note:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "13px"
  group:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
  task-mobile:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
  metadata:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "12px"
rounded:
  citation: "3px"
  control: "4px"
spacing:
  compact: "12px"
  group: "20px"
  wide: "28px"
  section: "40px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "12px 24px"
    height: "50px"
  citation:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.green}"
    rounded: "{rounded.citation}"
    padding: "0 6px"
---

# Design System: ytmd

## Overview

**Creative North Star: "Real videos, useful outcomes"**

The user replaced the single synthetic lesson with six real videos and requested prominent thumbnails, a short local-workflow outline, and a dark-mode toggle. Keep the established paper/navy/green/condensed-display identity and concise voice. Actual publisher imagery carries the visual weight. Every video has a task and short useful result; detailed plans and evidence remain optional.

## Colors

Green marks actions, timestamps, focus, and the three mechanism steps. Cool neutrals carry everything else. No large colored marketing sections.

Dark mode maps semantic roles to deep navy paper, pale ink, cool muted text, and mint green. Buttons use dark text on mint, not white; thumbnail overlays retain their own navy/white pair. The logo reverses to monochrome white, never the photographs. Both themes’ text/action pairs are checked against 4.5:1 AA contrast.

## Typography

Self-hosted Barlow Semi Condensed supplies the large headline. Inter supplies reading and controls. Monospace is only for timestamps and video durations. Group headings are 20px; task headings are 17px (18px on mobile), results 14px (15px on mobile). Source/coverage labels remain subordinate. The introduction becomes 16px below 600px.

## Layout

A 1080px maximum canvas with 24px gutters, falling to 20px below 600px. A two-column hero places the offer beside its explanation and the sole setup-copy action. The gallery has three columns above 900px, two on tablet, one below 600px, grouped as three builder and three business videos. Each image is 16:9. No card frames or nested panels.

The mechanism outline follows the gallery so a real thumbnail appears in the initial mobile viewport. Setup instructions and documentation follow. No sidebar, tabs, carousel, fixed-height source scroller, or command catalog. Native disclosures reveal each plan and its sources. Default page copy stays below 400 words for all six examples.

## Elevation & Depth

Flat surfaces with spacing and occasional thin boundaries. Only copy feedback floats, using `0 8px 24px rgb(0 0 0 / 15%)`. No decorative elevation.

## Shapes

Four-pixel control/thumbnail radii and native disclosure markers. Three numbered steps inside each plan communicate the proposed sequence. The source image is the artifact, not a decorative container. Theme icons are matching authored SVG strokes.

## Components

### Setup action

One green hero button copies the existing setup prompt. Success leaves instructions collapsed; failure opens them and selects the text for manual copying. No-JavaScript users get a hero setup link and native instructions. The separate header theme utility is not a competing primary action.

### Source citations

Real YouTube timestamps accompany short exact caption quotes. The full title, caption provenance, and selective reading coverage stay with the evidence. Direct `#evidence-VIDEO_ID` links open the corresponding plan and focus its evidence; no nested scroller.

### Disclosures

Six plan/source disclosures and setup instructions. The visible note identifies plans as adaptations, not speaker instructions or full reviews. No account, URL input, or simulated processing state.

### Theme utility

A labelled 44px header button follows system preference until the user chooses light or dark. A small pre-CSS script applies the saved `ytmd-theme` value without a light flash. Only this preference is persisted. Blocked storage leaves the current session usable. Without JS, CSS follows system dark mode and the inert toggle stays hidden.

## Do's and Don'ts

- **Do** pair each real video with one concrete task and short useful result.
- **Do** keep exact source quotes and required limitations available.
- **Do** make the next action obvious and singular.
- **Don't** restore the source sidebar, mode tabs, repeated marketing sections, or inline command catalog.
- **Don't** remove provenance labels to achieve a smaller word count.
