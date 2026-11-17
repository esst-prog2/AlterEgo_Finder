---
name: AlterEgo Finder
description: A lookalike finder scored like a competition round, with calibrated labels and the evidence behind them.
colors:
  scorecard-navy: "#1d3c78"
  scorecard-navy-deep: "#142c5a"
  paper: "#eef3f8"
  paper-raised: "#f8fbfd"
  grid-line: "rgba(29, 60, 120, 0.09)"
  grid-line-strong: "rgba(29, 60, 120, 0.22)"
  ink: "#1f2328"
  ink-soft: "#46505d"
  pencil: "#3d4450"
  same-person-green: "#1a7f37"
  alter-ego-gold: "#d4a72c"
  not-you-grey: "#8c959f"
  same-person-wash: "rgba(26, 127, 55, 0.13)"
  alter-ego-wash: "rgba(212, 167, 44, 0.24)"
typography:
  display:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "clamp(3rem, 7vw, 6rem)"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "clamp(1.9rem, 3.4vw, 2.6rem)"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "0.005em"
  title:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.02
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  label:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.03em"
  hand:
    fontFamily: "Kalam, cursive"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.45
  mono:
    fontFamily: "ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "0.92rem"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  none: "0px"
spacing:
  grid: "24px"
  gutter: "clamp(1rem, 4vw, 3rem)"
  card-pad: "clamp(1.25rem, 3vw, 2rem)"
  rule: "2px"
components:
  button-primary:
    backgroundColor: "{colors.scorecard-navy}"
    textColor: "{colors.paper-raised}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.55rem 0.9rem"
  button-primary-hover:
    backgroundColor: "{colors.scorecard-navy-deep}"
    textColor: "{colors.paper-raised}"
  button-primary-pressed:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.scorecard-navy}"
  card:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "{spacing.card-pad}"
  entry-box:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
  label-chip:
    textColor: "{colors.ink}"
    typography: "{typography.label}"
---

# Design System: AlterEgo Finder

## Overview

**Creative North Star: "The Scoresheet"**

AlterEgo Finder looks like the card an archery judge fills in: pale blue-white paper ruled in printed blue lines, every section framed by a navy rule, figures set in a condensed sports-form grotesk with tabular numbers, and a pencil hand for what was written down before a run. A face search is scored like a round: the similarity target is the target face, each candidate is a hit at its exact distance, and each claim about the program is an end on the scorecard, misses included.

The system serves four surfaces with one look: the promo page (docs/index.html), the local Streamlit app (app.py), the 30-second tour video (video/tour) and the downloadable report (summary.html). Density is moderate and print-like: generous paper, firm rules, no ornament that does not carry information. The only colour besides navy and ink belongs to the three labels, so a reader learns once that green, gold and grey mean Same person, Alter Ego and Not You, and can trust it everywhere.

Rejected: a dark "AI" void, glows and neon, purple or blue gradients, glass cards, rounded pill chips, and any colour used as decoration.

**Key Characteristics:**
- Paper and printed rules: a 24 px blue grid on the page ground, 2 px navy frames on every card.
- Condensed uppercase display type for names, headings, labels and figures; a plain grotesk for reading.
- Three label colours with one meaning each, plus the logo that contains them.
- Square corners throughout; depth by rules, not shadows.
- Numbers are tabular and exact, never rounded for effect.

## Colors

A cool, print-like palette: navy ink on blue-white paper, with three reserved signal colours.

### Primary
- **Scorecard Navy** (#1d3c78): every rule and frame, headings, links, primary buttons, focus rings, the grid's hue. It is the colour of the printed card itself.
- **Scorecard Navy Deep** (#142c5a): hover state of navy buttons only.

### Neutral
- **Paper** (#eef3f8): the page ground under the grid, entry boxes, code wells, table headers.
- **Paper Raised** (#f8fbfd): the surface of cards, panels and frames that sit on the paper.
- **Grid Line** (rgba(29, 60, 120, 0.09)) and **Grid Line Strong** (rgba(29, 60, 120, 0.22)): the printed ruling, table row rules, dashed dividers.
- **Ink** (#1f2328): body text and figures. **Ink Soft** (#46505d): secondary text, captions, notes. **Pencil** (#3d4450): handwritten predictions.

### Label colours
- **Same Person Green** (#1a7f37), **Alter Ego Gold** (#d4a72c), **Not You Grey** (#8c959f), with their washes (rgba(26, 127, 55, 0.13), rgba(212, 167, 44, 0.24)) for the rings' fills.

### Named Rules
**The Label Colour Rule.** Green, gold and grey mean Same person, Alter Ego and Not You, and appear nowhere else, with one named exception: the logo mark, which is the target in miniature.

**The One Navy Rule.** Navy is the only accent. No second brand colour, no gradients.

## Typography

**Display Font:** Barlow Condensed 600 and 700 (with Arial Narrow)
**Body Font:** Barlow 400, 500, 600 and 400 italic (with system-ui)
**Hand Font:** Kalam 400, for predictions written before a run
**Mono:** ui-monospace (Cascadia Mono, Consolas) for commands

**Character:** A sports-form condensed grotesk for everything that is named or counted, beside a calm humanist grotesk for reading; the hand appears only where something was genuinely written down beforehand. All fonts are open-licensed (SIL OFL) and shipped with the project, never fetched.

### Hierarchy
- **Display** (700, clamp(3rem, 7vw, 6rem), 1.02, uppercase): the product name in a masthead or end card.
- **Headline** (700, clamp(1.9rem, 3.4vw, 2.6rem), uppercase, navy): section titles.
- **Title** (700, 1.25rem, uppercase, navy): sub-sections, panel heads, step names.
- **Body** (400, 1.0625rem, 1.55, tabular figures): reading text, at most 68 characters a line.
- **Label** (600, 0.95rem, 0.03em, uppercase): label chips, buttons, table heads, toggles.

### Named Rules
**The Figures Rule.** Every number is set with tabular figures and shown at the precision it was measured (scores to four decimals); a figure that matters is set in the display face.

## Layout

A single sheet up to 76 rem wide with a fluid gutter (clamp(1rem, 4vw, 3rem)); sections are cards on the gridded paper, separated by generous space (clamp(2.5rem, 6vw, 4.5rem)). Inside a card, columns are divided by navy rules, not gaps. Below 900 px every multi-column card stacks to one column; the phone layout keeps the commands within one tap of the first screen. In the video the same sheet becomes a 1920 x 1080 frame on the same paper and grid.

## Elevation & Depth

Flat print. Structure comes from 2 px navy rules and the paper's grid; a card may carry one faint drop beneath it (0 1px 0 navy, 0 10px 28px -18px rgba(29, 60, 120, 0.45)) to lift it off the grid, and nothing else casts a shadow.

### Named Rules
**The Ruled Frame Rule.** If something needs separating, rule it. Never a shadow, a glow or a blur for depth.

## Shapes

Square corners everywhere (0 px): cards, buttons, inputs, code wells, video frames. Circles are reserved for meaning: label dots, the target's rings and hits, the switch knob, the logo. Dividers inside cards are 1.5 px, dashed for soft breaks.

## Components

### Buttons
- **Shape:** square (0 px), 2 px navy border.
- **Primary:** navy fill, raised-paper text, label type, padding 0.55rem 0.9rem.
- **Hover / Focus:** fill deepens to navy deep; focus is a 3 px navy outline offset 3 px.
- **Pressed / toggled:** the colours invert (raised paper with navy text), as on the Copy and operating-system toggles.

### Label chips
- **Style:** a dot in the label's colour with a 1.5 px ink outline, then the label's name in label type, uppercase. The dot carries the colour; the text stays ink.
- **In the Streamlit app**, where a drawn dot is not available, the name sits in bold ink on a light wash of its label colour (Streamlit's own highlight). The text never takes the label colour itself.

### Cards / Containers
- **Corner Style:** square.
- **Background:** paper raised on the paper ground.
- **Border:** 2 px navy, with the single faint drop described under Elevation.
- **Internal Padding:** clamp(1.25rem, 3vw, 2rem).

### Inputs / Fields
- **Style:** paper fill, 2 px navy frame, square; commands and code in mono on paper.
- **Focus:** the 3 px navy outline.

### The Target Face (signature)
The similarity target: you at the centre as a navy cross, the Same person ring (green, with its wash) at 1 minus the upper threshold, the Alter Ego ring (gold) at 1 minus the lower threshold, every candidate a hit at exactly 1 minus its score, the rest of the dataset a grey cloud. Direction means nothing, and every surface says so.

### The Logo (signature)
The target in miniature beside the name: a gold ring with its wash, a green ring with its wash, a navy cross at the centre and one green hit inside the green ring; then "AlterEgo Finder" in display type, uppercase, on two lines. Files: video/tour/assets/logo-mark.svg. It sits once per surface: in the page's masthead, at the top of the app's sidebar, in the corner of each video scene and beside the name on its end card, and in the report's header.

## Do's and Don'ts

### Do:
- **Do** put every surface on the same paper (#eef3f8) and grid, framed by 2 px navy rules.
- **Do** use the label colours only for Same person, Alter Ego and Not You, and inside the logo.
- **Do** show scores to four decimals with tabular figures, next to the label they produce.
- **Do** credit every photograph where it appears (author and licence).
- **Do** ship the fonts with the project (docs/fonts, the app's static folder, video/tour/assets/fonts).

### Don't:
- **Don't** use rounded corners, pill chips or shadows for depth.
- **Don't** introduce a second accent colour or a gradient.
- **Don't** colour a whole label word in its label colour on a light ground when the gold would fail contrast: the dot carries the colour.
- **Don't** place a title over a dimmed screenshot or a dark void behind the product.
