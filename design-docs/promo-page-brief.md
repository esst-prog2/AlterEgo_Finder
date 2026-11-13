# Design brief: AlterEgo Finder promo page

From Impeccable's `shape`, confirmed by the user on 2026-11-13. Content: [promo-page-content.md](promo-page-content.md). No code yet.

## 1. Job and audience

Classmates, the teacher and data science students, reading on a laptop or a phone before the final demo on 1 or 8 December 2026. Mode: persuade. They must leave believing the labels: the program knows how much to trust its own answer.

## 2. Outcome and proof

- Within the first screen, a visitor knows what it does, who it is for and how to try it.
- By the end, they trust *Same person*, *Alter Ego* and *Not You*.
- Proof is the approved receipts ledger: real numbers from PLANNING_LOG.md only, failures included. No users, testimonials or benchmarks are invented.

## 3. Selected direction: The Scoresheet

- World: an archery target face and a competition scorecard. The target is the real similarity rings for an LFW example: the inner *Same person* ring and the *Alter Ego* band. The scorecard holds the receipts, each claim an "end": what was written before the run, the measured result, its source, and a check command where one exists.
- Colours: a pale card ground with a printed blue grid and pencil-dark ink. Green, gold and grey are reserved for the three labels only.
- First screen: the target on one side; on the other, the scorecard header with what it does, who it is for, "your photo never leaves your machine", and Try it locally as the card's entry box.
- Carried over from the challengers it was weighed against:
  - Arcade cabinet: the label colours are law, used only to mean the three labels, never as decoration.
  - Street-fashion spread: every number carries a call-out to its source.
  - Wood-type manifesto: no photographs at all; type and figures carry the page, so no face is used as decoration.
  - Curved crease: the threshold ring radii set the page's measures.
  - Glaze shelf: each result names its dataset beside it.
- Built in code (no image generation in this session); the ambition goes into the direction contract written before building.
- Roll: seed:8e6a59af0615c870, the assigned direction (4th of 7 grounded candidates).

## 4. Scope and boundaries

- One static HTML/CSS page in `docs/`, production quality.
- Untouched: the program itself and the approved content.
- Anti-goals: hype, startup gloss, gradients and glow; faces as decoration or any photo of the author; gamification, so labels never become points or a high score.

## 5. States and ranges

- The ledger has 7 rows, each claim 1 to 2 lines; "record only" rows look different from checkable ones.
- The target shows about 10 named hits and a faint cloud of the rest.
- On a phone, the target stacks above the scorecard, and the ledger rows become cards.

## 6. Interaction and layout

- Reading order: first screen (target and header), how it works, the receipts as scorecard ends, privacy, try it locally, limits with model-card headings, footer.
- Signature interaction: hovering or focusing a ledger row lights its zone on the target.
- Works without motion and with a keyboard.

## 7. Constraints and open decisions

- Any pool photo visible on the page is credited beside it; with "no photographs", the target shows names, not photos.
- The LFW example is still to be picked (a non-politician).
- Publishing needs the branch merged to `main` and GitHub Pages enabled in the repository settings.
