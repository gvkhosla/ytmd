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

**Creative North Star: "The source review, distilled"**

The user rejected the previous site's complexity and noisy copy. Keep the established cool paper, navy text, green actions, and condensed display face; remove competing demonstrations and secondary surfaces. Show one task and its useful answer. Evidence stays inspectable without being permanently on screen.

## Colors

Green is reserved for the setup action, timestamps, and focus. Cool neutrals carry everything else. Source passages get a gentle tonal change when selected. No large colored marketing sections are needed.

## Typography

Self-hosted Barlow Semi Condensed supplies the single large headline. Self-hosted Inter supplies reading and controls. Monospace is used only for timestamps. The introduction becomes 16px below 600px. Compact labels stay subordinate; the headline supplies the large hierarchy step.

## Layout

One left-aligned column, at most 680px wide. Viewport gutters are 24px, falling to 20px below 600px. The flow is offer, one example, setup, then documentation links. The setup button spans the column on small screens.

No sidebar, task tabs, nested review grid, fixed-height source scroller, or feature tour. Additional evidence and setup text use native disclosures; CLI commands remain in linked documentation.

## Elevation & Depth

Flat surfaces with spacing and occasional thin boundaries. Only copy feedback floats, using `0 8px 24px rgb(0 0 0 / 15%)`. No decorative elevation.

## Shapes

Small-radius controls and a simple question surface. Native disclosure markers remain native. The three numbered steps communicate a procedure rather than decorating sections.

## Components

### Setup action

One green button copies the existing setup prompt. Success leaves instructions collapsed; failure opens them and selects the text for manual copying. No-JavaScript users can open and copy the instructions directly.

### Source citations

Real fragment links open the source disclosure and focus their exact passage. Native history and keyboard navigation remain intact. Source text is not truncated or nested inside another scroller.

### Disclosures

Source passages and setup instructions are the only disclosures. The source is visibly labelled synthetic; the expanded view explains selective coverage. No account, URL-input, or simulated processing state is introduced.

## Do's and Don'ts

- **Do** explain one concrete use case before offering more choices.
- **Do** keep exact source quotes and required limitations available.
- **Do** make the next action obvious and singular.
- **Don't** restore the source sidebar, mode tabs, repeated marketing sections, or inline command catalog.
- **Don't** remove provenance labels to achieve a smaller word count.
