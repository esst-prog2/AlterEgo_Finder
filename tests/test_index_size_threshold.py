"""threshold_high must be fitted to the top-1 absent-stranger distribution at
the deployed index size, not to pairwise impostor scores (change
fit-high-threshold-to-index-size; HW4 spike, data/spike_results.json).

Synthetic and hermetic: random unit vectors stand in for embeddings. 64
dimensions widens the cosine spread so the pairwise 1%-FAR threshold lands
near ~0.28, the same scale the spike saw on real ArcFace embeddings.
"""

import numpy as np

from face_pipeline.calibration import (
    compute_far_threshold,
    compute_index_high_threshold,
    sample_pairs,
)
from match import HIGH_CONFIDENCE, classify

INDEX_SIZE = 500
DIM = 64
QUERIES = 200
THRESHOLD_LOW = 0.0  # only the HIGH_CONFIDENCE boundary is under test


def _unit_vectors(rng, n):
    v = rng.normal(size=(n, DIM))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def _high_confidence_rate(scores, threshold_high):
    labels = [classify(float(s), THRESHOLD_LOW, threshold_high) for s in scores]
    return float(np.mean([label == HIGH_CONFIDENCE for label in labels]))


def test_absent_stranger_is_not_high_confidence_against_500_face_index():
    rng = np.random.default_rng(0)
    index = _unit_vectors(rng, INDEX_SIZE)
    calibration_strangers = _unit_vectors(rng, QUERIES)
    query_strangers = _unit_vectors(rng, QUERIES)  # disjoint from both sets above

    # Original rule: 1% FAR on pairwise impostor scores.
    _, inter = sample_pairs({f"p{i}": [e] for i, e in enumerate(calibration_strangers)})
    pairwise_high = compute_far_threshold(inter)

    fitted_high = compute_index_high_threshold(calibration_strangers, index)

    top1 = (query_strangers @ index.T).max(axis=1)

    # Guard, not the expected value: the synthetic data must reproduce the
    # spike's failure (198/200 HIGH_CONFIDENCE at N=500), or the test proves nothing.
    assert _high_confidence_rate(top1, pairwise_high) > 0.5

    # Expected value (PLANNING_LOG.md, 2026-10-08): the spec's 1% target FAR,
    # i.e. at most 2 of 200 absent strangers labelled HIGH_CONFIDENCE.
    assert _high_confidence_rate(top1, fitted_high) <= 0.01


def test_high_threshold_grows_with_index_size():
    rng = np.random.default_rng(0)
    index = _unit_vectors(rng, 5000)
    strangers = _unit_vectors(rng, QUERIES)

    # Nested indices (first 50/500/5000), as in the spike.
    highs = [compute_index_high_threshold(strangers, index[:n]) for n in (50, 500, 5000)]

    # Expected value (PLANNING_LOG.md, 2026-10-08): the spec scenario
    # "High threshold grows with index size".
    assert highs[0] <= highs[1] <= highs[2]
