---
name: ytmd
description: A clear source review, with useful understanding beside its evidence.
colors:
  paper: "#f4f6fa"
  white: "#ffffff"
  ink: "#172638"
  muted: "#526071"
  green: "#195e54"
  green-hover: "#124b43"
  lime: "#e2ec70"
  source: "#edf1f5"
  selected: "#e3eee8"
  line: "#d7dfe7"
typography:
  display:
    fontFamily: "'Barlow Semi Condensed', sans-serif"
    fontSize: "clamp(4rem, 7vw, 6rem)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "'Barlow Semi Condensed', sans-serif"
    fontSize: "clamp(2.5rem, 4vw, 3.5rem)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.025em"
  body:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  evidence:
    fontFamily: "InterVariable, system-ui, sans-serif"
    fontSize: "14px"
    lineHeight: 1.7
  timestamp:
    fontFamily: "'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
    fontSize: "13px"
    fontWeight: 500
rounded:
  citation: "3px"
  control: "4px"
spacing:
  tight: "8px"
  compact: "16px"
  group: "24px"
  wide: "48px"
  section: "80px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "12px 20px"
    height: "50px"
  button-primary-hover:
    backgroundColor: "{colors.green-hover}"
    textColor: "{colors.white}"
  citation:
    backgroundColor: "#eaf0ed"
    textColor: "{colors.green}"
    rounded: "{rounded.citation}"
    padding: "0 5px"
  citation-selected:
    backgroundColor: "{colors.green}"
    textColor: "{colors.white}"
  source-passage:
    backgroundColor: "{colors.source}"
    padding: "20px 24px"
  source-passage-selected:
    backgroundColor: "{colors.selected}"
---

# Design System: ytmd

## Overview

**Creative North Star: "The source review"**

An open, precise review surface: readable evidence, visible annotations, and an explanation that does not lose its source. The user chose this direction for the website redesign. Bold condensed headings establish the larger narrative; the review itself is deliberately quieter and denser.

The light field suits reading and comparing passages alongside an existing agent in an ordinary desktop or mobile browsing session. Contrast comes from navy structural areas and a green installation region, not decorative chrome.

**Key Characteristics:**
- Large condensed headlines, restrained evidence typography.
- Open review columns and inspectable timestamp annotations.
- Cool neutrals, deep green, and a pale lime adaptation surface.
- Plain, legible controls with progressive enhancement.

## Colors

Deep green carries actions, timestamps, and selection. Navy carries text and the review header. Cool paper and source surfaces separate reading regions; lime signals text selection and informs the lighter adaptation surface. Green sections use green-tinted near-white supporting text.

**The Evidence State Rule.** Selected evidence uses a full tonal change and a thin inset outline, not a thick colored side stripe. Its corresponding citation also changes state.

## Typography

Barlow Semi Condensed SemiBold is self-hosted for display and section headings. Inter Variable is self-hosted for reading and controls. Both font licenses ship beside their files. Monospace is reserved for timestamps and commands, not general-purpose technical decoration.

The frontmatter records the default desktop roles. At 639px and below, the display becomes `clamp(3.5rem, 15vw, 5rem)`, source and answer copy becomes 15px, and ordinary explanatory copy is 16px. Compact labels do not compete with the display hierarchy. Headings balance their wrapping; code wraps rather than pushing the page sideways.

## Layout

The container is at most 1320px including horizontal padding: 48px by default, 32px below 1100px, and 22px below 639px. Sections use generous 48–88px separation while evidence groups remain compact.

The review is a full-width shared surface, not nested cards. Desktop source/answer columns use a `.85fr / 1.25fr` ratio. At 800px and below, the enhanced review puts the answer before the source; JavaScript moves the DOM to keep keyboard order consistent. Without JavaScript, source and answers remain in their natural, visible document order.

Source text can scroll independently, with a visible navigation hint. Mobile reading does not require horizontal scrolling. Installation alternatives use native disclosures.

## Elevation & Depth

Most surfaces are flat, separated by tone and thin boundaries. Only transient feedback and the mobile navigation use soft, offset neutral shadows: `0 8px 24px rgb(0 0 0 / 15%)` for the toast and the same geometry at 10% for navigation.

**The Flat Review Rule.** Evidence gets no decorative elevation. Its selection outline communicates state, not a lifted card.

## Shapes

Review boundaries and source rows have square structural edges. Buttons and installation panels use a small control radius; citations use a slightly smaller radius. Native disclosure markers remain native. The few authored icons are small, consistent outline SVGs.

## Components

### Buttons and navigation

Primary actions are green with white text and a 50px minimum height. Hover deepens green; keyboard focus is a visible three-pixel outline. Copy controls disable while awaiting the clipboard, then restore. Failure selects the source text where possible and reports a manual recovery path. Mobile menu entries and copy buttons have 48px minimum heights.

### Task tabs

Three text tabs share one baseline. Active state is green, semibold, and underlined. Left/Right wrap through tabs; Home/End choose the endpoints. Selection changes both the answer and its evidence scope. Only the active tab is in the ordinary Tab sequence.

### Citations and passages

Citations are real fragment links. Enhanced activation selects, scrolls to, and focuses the matching source passage; small-screen navigation brings the source area into view. Deep links select the appropriate example. The source count describes the selected subset, not full-video coverage.

### Adaptation annotations

A pale lime-tinted block distinguishes proposed adaptations from source-derived guidance. It uses plain language and a short descriptive label, not a decorative icon or numbered badge.

### Disclosures and feedback

Native `details` preserves terminal installation, the task prompt, and reference content without JavaScript. Copy feedback uses a polite status region. No modal or focus trap is required.

The review's single entrance grammar is a short 280ms exponential ease-out with a small vertical move and clip adjustment. Content is visible before enhancement; reduced-motion users receive no entrance animation and immediate source navigation.

## Do's and Don'ts

### Do:
- **Do** keep source, interpretation, and adaptation visually distinguishable.
- **Do** preserve exact source wording and visibly label synthetic demonstrations.
- **Do** keep responsive visual and keyboard reading order aligned.
- **Do** keep instructions usable without JavaScript.

### Don't:
- **Don't** substitute a filesystem mockup for a useful example.
- **Don't** use false progress, fabricated testimonials, or a URL input that cannot process videos.
- **Don't** turn source excerpts into a grid of decorative cards.
- **Don't** use display typography for the dense evidence-reading role.
