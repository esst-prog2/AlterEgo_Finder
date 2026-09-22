## Context

Builds on all four archived changes (`face-embedding`,
`face-matching-cli`, `threshold-calibration`, `model-weight-delivery`).
This is the last piece of README section 3's "First useful version" scope
still missing. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Implement `summary-report` and the ADDED `face-matching-cli`
  requirement: `match.py` writes a self-contained HTML report after a
  successful match.

**Non-Goals:**
- A live drag-and-drop UI (Gradio or otherwise) — discussed separately,
  deferred until after this.
- A configurable top-K CLI flag — a module constant is proportionate for
  now; add a flag later only if a real need shows up.
- Visual polish beyond clean and readable — this is a course project
  report, not a product surface.

## Decisions

### Plain string templating, no Jinja2
Consistent with this project's minimal-dependency footprint
(`opencv-python` + `numpy` only otherwise): HTML is built with f-strings
in `face_pipeline/report.py`, not a templating engine. The page is small
and fixed-shape enough that this doesn't get unreadable.

### Images embedded as base64 JPEG data URIs
Read via `cv2.imencode('.jpg', image)` rather than trying to preserve and
sniff the original file's format/extension — guarantees a consistent,
predictable embeddable format regardless of whether the source was a
`.jpg`, `.jpeg`, or `.png`. Uses stdlib `base64`, no new dependency.

### Top-K cap: a module constant
`REPORT_TOP_K = 10` in `face_pipeline/report.py`. At the "10,000+ indexed
vectors" scale this project targets, embedding every ranked candidate's
image in one HTML file isn't practical — 10 is enough to visually confirm
the top match and a few runners-up without producing an unreasonably
large file.

### Report path: a plain default, not derived from `--dataset`
Unlike `--config` (which defaults to `<dataset>/../config.json`),
`--report-out` defaults to the literal `data/results/summary.html` —
matching README section 1's demo exactly, which treats this as a fixed
conventional location, not something tied to which dataset was queried.
The parent directory is created (`mkdir(parents=True, exist_ok=True)`) if
it doesn't exist.

### Confidence status is color-coded
`HIGH_CONFIDENCE` / `LOW_CONFIDENCE` / `NO_MATCH` get distinct colors
(green / amber / gray) in the rendered report, directly supporting
README section 4's acceptance criterion that a below-threshold result is
*explicitly flagged*, not just quietly listed with a lower number.

## Risks / Trade-offs

- [Risk] Embedding full-resolution images inflates the report file size
  (a handful of real photos could be a few MB total). → Accepted for now;
  not spec-required to thumbnail, and this project's test fixtures are
  already small (150-350KB range). Revisit if it becomes a real problem.
- [Risk] `cv2.imencode` re-encoding discards any embedded EXIF
  orientation metadata from the original file. → Not expected to matter
  for this project's fixtures/use case; noting it rather than silently
  ignoring it.

## Migration Plan

None — purely additive. Existing `match.py` invocations without
`--report-out` get the new default report path; nothing about existing
stdout output or exit codes changes.
