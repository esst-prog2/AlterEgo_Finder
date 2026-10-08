## Context

See proposal.md - Why. `calibrate.py` derived both thresholds from pairs
sampled inside `--calibration-dir` (`compute_thresholds` in
`face_pipeline/calibration.py`). It never saw the dataset `match.py`
searches, so it could not know the index size N that the high threshold
depends on.

## Goals / Non-Goals

**Goals:**
- `threshold_high` is the 1% false-accept point of absent strangers' top-1
  scores against the real dataset index.
- Reuse the existing `compute_far_threshold` and the dataset index cache
  (`get_or_build_index`, shared with `match.py`).
- A hermetic test of the rule, with no LFW download.

**Non-Goals:**
- Changing `threshold_low` (stays at the pairwise EER point).
- `match.py` detecting that `config.json` is stale for a grown dataset.
- Separate thresholds for candidates below rank 1.
- LFW-scale tests in the test suite (`spike_eval.py` covers real data).

## Decisions

1. **Fit against the real dataset index, not a simulated N.** `calibrate.py`
   takes `--dataset` and loads its index. Alternative: an `--index-size N`
   flag with a synthetic index drawn from calibration data. Rejected: the
   calibration set is too small to supply N distinct impostors, and the real
   index's score distribution is the one `match.py` actually sees.
2. **Calibration identities serve as the absent strangers.** README requires
   them to be disjoint from the dataset, so every calibration image is a
   valid absent-stranger query. Alternative: leave-one-identity-out over the
   dataset itself, which would remove the need for a calibration directory
   but costs N searches; possible follow-up.
3. **`--dataset` is required, with no silent fallback to the pairwise rule.**
   A fallback would quietly reproduce the 99%/100% false-accept failure the
   spike measured. Callers updated: CLI tests, run-alterego-finder skill.
4. **The promise sits in one line.** `top1_scores` is the vectorized
   `(queries @ index.T).max(axis=1)`, and `compute_index_high_threshold`
   applies `compute_far_threshold` to its output. Replacing the max with a
   single column turns it back into a pairwise score, which is the mutation
   the red/green check uses.
5. **Keep the clamp `threshold_high = max(fitted, threshold_low)`**, per the
   spec scenario that the high threshold is at least as strict as the low
   one. On tiny datasets (the 3-face test fixture) the clamp is what applies.
6. **The test uses synthetic 64-d unit vectors.** 64 dimensions put the
   pairwise 1% point near 0.28, the scale of the spike, without real images.
   The expected value (at most 1%, i.e. 2 of 200 absent strangers
   HIGH_CONFIDENCE at N=500) was chosen by the user from the spec's target
   FAR and the spike's 198/200 at N=500 (PLANNING_LOG.md, 2026-10-08), not
   derived by running the code.

## Risks / Trade-offs

- [Fewer than 100 stranger images make the 1% point coarse: the threshold
  becomes the highest top-1 score seen] → use 200+ calibration images for
  real use, as the spike did.
- [config.json goes stale when the dataset grows, and a too-low threshold
  brings false HIGH_CONFIDENCE labels back] → README says to re-run
  calibration; a staleness check in `match.py` is follow-up work.
- [The test sits exactly at its bound: seed 0 gives 2/200] → the seed is
  fixed; if it ever fails after a change, raise the query count rather than
  loosen the bound.
- [Synthetic vectors are not ArcFace embeddings] → `spike_eval.py` measures
  the real-data behavior.

## Migration Plan

Re-run `python calibrate.py --calibration-dir <dir> --dataset <dir>`; any
existing `data/config.json` is stale. The config format is unchanged (same
two keys), so rollback is a plain revert.
