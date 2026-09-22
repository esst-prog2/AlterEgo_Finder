## Why

README's "First useful version" scope (section 3) lists four bullets;
three are implemented and tested, but "automated generation of a
self-contained `summary.html` report" is still missing — `match.py`
currently only prints to stdout. This is the last piece needed to call
the MVP complete against the project's own definition of done.

## What Changes

- Add a new capability, `summary-report`: renders a self-contained HTML
  report — the query image, the top-ranked candidates, and each
  candidate's confidence status — as its own testable rendering behavior.
  "Self-contained" means no external asset files: images are embedded as
  base64 data URIs directly in the HTML, so the report opens correctly
  straight from disk with no local server.
- **ADDED**: `match.py` now also writes this report as a side effect of a
  successful match (query image had a detectable face), to
  `data/results/summary.html` by default, overridable via `--report-out`.
  Not written on the no-face-detected error path — there's nothing to
  report.
- Capped to the top-K ranked candidates, not the entire dataset ranking —
  at the "10,000+ indexed vectors" scale this project targets, embedding
  every candidate's image in one HTML file isn't practical.

## Capabilities

### New Capabilities
- `summary-report`: renders a self-contained HTML report (query image +
  top-K ranked candidates + confidence status) from a query image and a
  set of ranked match results.

### Modified Capabilities
- `face-matching-cli`: gains a new requirement — `match.py` writes the
  visual report after a successful match. The existing "Ranked match
  output" (stdout) requirement is unchanged; this is an additional output
  channel, not a replacement.

## Impact

- New module: `face_pipeline/report.py` — pure rendering: given a query
  image path and ranked results, produces the self-contained HTML.
- `match.py`: calls into it after computing results; new `--report-out`
  CLI option (default `data/results/summary.html`).
- No new dependencies — stdlib `base64` + plain string templating, no
  Jinja2 or similar, consistent with this project's minimal-dependency
  footprint (`opencv-python` + `numpy` only, otherwise stdlib).
