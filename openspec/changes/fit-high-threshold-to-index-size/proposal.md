## Why

`threshold_high` is calibrated as a 1% false-accept rate on *pairs*, but
`match.py` applies it to the *top-1* score of a search over N indexed faces,
where a stranger's false-accept rate grows roughly as 1 − 0.99^N. The HW4
spike (issue #4, `spike_eval.py`, `data/spike_results.json`) measured it on
LFW: calibrating on 200 held-out identities gave `threshold_high` = 0.2017
(exactly 1% pairwise FAR), yet for 200 queries of people absent from the
index, the top-1 score reached `threshold_high` for:

| Index size N | Absent strangers labelled HIGH_CONFIDENCE |
|---|---|
| 50 | 33.0% (66/200) |
| 500 | 99.0% (198/200) |
| 5000 | 100.0% (200/200) |

So with a realistically sized dataset, every stranger gets a HIGH_CONFIDENCE
alter ego. The 1% operating point of the top-1 stranger distribution moves
with N: ~0.28 at N=50, ~0.44 at N=5000.

## What Changes

- `threshold_high` is fitted to the distribution of top-1 (max-over-index)
  scores of queries whose identity is absent from an index of the dataset's
  actual size, instead of to pairwise impostor scores.
- `threshold_low` stays at the pairwise EER point (out of scope here).
- Implementation in `calibrate.py` is follow-up work; this change records the
  requirement and the evidence for it.

## Capabilities

### New Capabilities

### Modified Capabilities
- `threshold-calibration`: the high threshold's operating point moves from the
  pairwise inter-class distribution to the top-1 absent-stranger distribution
  at the deployed index size.

## Impact

- `calibrate.py` / `face_pipeline/calibration.py`: must know the target index
  size (or the dataset itself) and simulate rank-1 search with held-out
  strangers.
- `data/config.json`: values change per dataset size; existing configs are
  stale for any index larger than a handful of faces.
- README section 3 documents the new calibration rule.
