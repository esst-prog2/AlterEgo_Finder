# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Promo page: plain static HTML/CSS, one hand-written page with no build step, served by GitHub Pages from `docs/` on `main`. The program itself is Python with a local Streamlit page; this stack covers the promo page only.

## Users

- Classmates, the teacher and data science students in the ELTE Advanced Programming course (2026/27), who read the page and score the program at the final demo on 1 or 8 December 2026.
- Anyone curious which public figures they resemble, willing to run a program on their own computer.

## Product Purpose

AlterEgo Finder finds the closest public figures to a face in a photo. Each of the ten closest gets a similarity score and a plain label, *Same person*, *Alter Ego* or *Not You*, from thresholds calibrated on held-out strangers. Success is an answer the user can trust: a lookalike when there is one, and *Not You* when there is not.

## Positioning

Most lookalike apps always name someone. AlterEgo Finder says *Not You* when it should, shows the evidence behind its labels (predictions logged before runs, failures included), and never sends the photo anywhere: it runs entirely on the user's own machine.

## Operating Context

- Runs locally: a Streamlit page on localhost (`streamlit run app.py`) and a CLI (`match.py`), on the same pipeline.
- One-command setup: `python setup_data.py` downloads LFW and builds the default dataset of 500 LFW faces and the calibration set (about 3.5 minutes). `python setup_data.py --wikidata` optionally builds a pool of 500 public figures from Wikimedia Commons (about 30 minutes).
- The final demo is a 5-minute slide presentation with screenshots, not a live run.

## Capabilities and Constraints

- Detection with YuNet (largest face; photos that are too large, or turned by 90, 180 or 270 degrees, are handled), 512-number embeddings with ArcFace, cosine similarity ranking, two calibrated thresholds, a similarity target chart, and a self-contained `summary.html` report.
- Labels: *Same person*, *Alter Ego*, *Not You* on the page; `HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, `NO_MATCH` in the CLI and report.
- The upper threshold is fitted to strangers' best matches at the dataset's size; the lower one is the pairwise equal-error-rate point.
- The pool: adults known to the public, no politicians, each photo's author and licence credited.
- Works from any install folder, including paths with non-ASCII characters.
- No hosted version: running locally is the design, not a missing feature.
- Limits: tilts near 45 degrees stay poor; one photo per person in the pool; *Alter Ego* means "the closest public figure, and not you", not a striking likeness.

## Brand Commitments

- Name: AlterEgo Finder.
- The three labels are named *Same person*, *Alter Ego* and *Not You* wherever users see them.
- Promise: the photo never leaves the user's machine.

## Evidence on Hand

- Measured results with their dates in `PLANNING_LOG.md`, including predictions written before runs and negative results: the HW4 threshold spike (`data/spike_results.json`), the multi-photo spike (`data/spike_multiphoto_results.json`), the rotation fix, and the byte-identical checks after each fix.
- 271 automated tests (`python -m pytest tests/`).
- The approved content design for the promo page: `design-docs/promo-page-content.md`.
- No users, testimonials, customers or press exist; none may be invented.

## Product Principles

- Tell the user how much to believe the answer: calibrated labels, not just a name.
- Show the evidence, including what failed.
- Nothing about the user leaves their machine.
- Every number shown matches the recorded measurement.

## Accessibility & Inclusion

- The promo page must read well on a phone.
- Nothing personal about the project's author appears on public pages: no photo, crop or match result.
