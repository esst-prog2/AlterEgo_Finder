## Why

`match.py` currently prints raw similarity scores with no way to tell a
genuine match from noise. README's acceptance criteria require that a
low-similarity result be explicitly flagged as unreliable rather than
presented as a match, and the demo's stated output includes a categorical
match quality (`HIGH_CONFIDENCE` / `LOW_CONFIDENCE` / `NO_MATCH`). This
change adds a calibrated confidence classification on top of Change 1's
ranking.

## What Changes

- Add a `data/calibration/` dataset layout: LFW-style identities fully
  disjoint from `data/celebrities/`, used only for threshold calibration
  (never indexed for matching).
- Add `calibrate.py`, an offline script that samples same-person
  (intra-class) and different-person (inter-class) pairs from
  `data/calibration/`, computes their similarity distributions, and derives
  **two** thresholds from the ROC curve:
  - a lower threshold at the equal-error-rate (EER) point — the
    `NO_MATCH` / `LOW_CONFIDENCE` boundary (this is the `0.68` already
    named in README);
  - a higher threshold at a low false-accept-rate operating point — the
    `LOW_CONFIDENCE` / `HIGH_CONFIDENCE` boundary.
- `calibrate.py` writes both thresholds to `data/config.json`.
- **MODIFIED**: `match.py`'s ranked output now also prints, per candidate,
  a `HIGH_CONFIDENCE` / `LOW_CONFIDENCE` / `NO_MATCH` label based on the
  two thresholds. Thresholds default from `data/config.json` when present,
  with `--threshold-low`/`--threshold-high` CLI overrides available.
- **Out of scope for this change**: the `summary.html` report — a later
  change.

## Capabilities

### New Capabilities
- `threshold-calibration`: offline derivation of the two confidence
  thresholds from a held-out, disjoint calibration dataset, written to
  `data/config.json`.

### Modified Capabilities
- `face-matching-cli`: the "Ranked match output" requirement changes —
  each ranked candidate now carries a confidence label, not just a raw
  score, and the CLI gains threshold-related options.

## Impact

- New script: `calibrate.py`.
- New shared module(s) under `face_pipeline/` for pair sampling, ROC/EER,
  and FAR-based threshold computation, reused by `calibrate.py` (and
  callable from tests without re-running the full CLI).
- New on-disk artifacts: `data/calibration/` (user-supplied, disjoint LFW
  identities) and `data/config.json` (calibration output).
- `match.py`'s output format changes (adds a classification label per
  line) — existing consumers of Change 1's plain ranked output will see a
  different line format.
