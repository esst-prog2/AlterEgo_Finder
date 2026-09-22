## Context

Builds directly on `add-face-matching-cli` (archived): the `face-embedding`
and `face-matching-cli` capabilities already exist and are not re-derived
here. See proposal.md for motivation, and the earlier explore-mode
discussion (logged in PLANNING_LOG.md) for why two thresholds are needed
instead of the single `0.68` value README names.

## Goals / Non-Goals

**Goals:**
- Implement `threshold-calibration` (EER + FAR-based thresholds from a
  held-out calibration set, written to `data/config.json`).
- Modify `face-matching-cli` so ranked output carries a confidence label.

**Non-Goals:**
- `summary.html` report generation — a later change.
- Re-validating the embedding model's overall discriminative quality —
  calibration measures whatever the existing `face-embedding` capability
  produces, it doesn't change or judge it.

## Decisions

### Two thresholds from one ROC curve
Both thresholds come from the same intra-/inter-class similarity
distributions computed once per calibration run:
- **Low threshold** = the EER point (intra-class false-reject rate =
  inter-class false-accept rate). This is README's existing `0.68`
  concept — the `NO_MATCH` / `LOW_CONFIDENCE` boundary.
- **High threshold** = the score at a **1% false-accept-rate** operating
  point on the inter-class distribution — i.e., at or above this score,
  at most 1% of different-person pairs in the calibration set would score
  that high. This is a standard, conservative operating point in face
  verification (favoring precision over recall for the "high confidence"
  claim). The 1% figure is a reasonable default, not derived from
  anything in README; it's a single named constant, easy to change later
  if a different false-accept tolerance is wanted.

### Pair sampling
All intra-class pairs (every same-person pair within each identity folder)
are used. Inter-class pairs are sampled: since the number of possible
different-person pairs grows quadratically, sampling is capped at a fixed
count (e.g. a few thousand) drawn uniformly across identity pairs, to keep
calibration runtime bounded without needing every possible cross-identity
pair.

### Module layout
- `calibrate.py` — thin CLI entrypoint (mirrors `match.py`'s relationship
  to `face_pipeline/index.py`).
- `face_pipeline/calibration.py` — pair sampling, ROC/EER computation, and
  FAR-based threshold search. Reuses `face_pipeline.embedder.extract_embedding`
  for the pairwise embeddings; does not duplicate detection/embedding logic.

### `data/config.json` schema
```json
{"threshold_low": 0.68, "threshold_high": 0.83}
```
This supersedes the earlier, single-key sketch (`{"threshold": 0.68}`)
from the pre-implementation discussion, now that two thresholds are
needed.

### match.py behavior when no threshold source is available
If `data/config.json` doesn't exist and neither `--threshold-low` nor
`--threshold-high` is passed, `match.py` prints a clear error (analogous
to the no-face-detected error) and exits non-zero, rather than guessing a
high-threshold default with no calibration behind it. Change 1's plain
ranking behavior is not silently substituted — classification is either
done properly or the CLI says why it can't.

## Risks / Trade-offs

- [Risk] A small calibration set makes the 1%-FAR high threshold noisy
  (few inter-class pairs to resolve a 99th-percentile point precisely).
  → Mitigation: use all available inter-class pairs up to the cap;
  document that more calibration identities improve threshold stability.
  Not spec-enforced — a course-project-scale dataset is expected to be
  small.
- [Risk] The 1% FAR constant is a judgment call, not derived from README.
  → Mitigation: named constant in one place (`face_pipeline/calibration.py`),
  easy to revisit.
