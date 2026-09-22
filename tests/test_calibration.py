from pathlib import Path

import numpy as np
import pytest

from face_pipeline.calibration import (
    compute_eer_threshold,
    compute_far_threshold,
    compute_thresholds,
    embed_calibration_dataset,
    sample_pairs,
)

FIXTURES = Path(__file__).parent / "fixtures"
CALIBRATION_DIR = FIXTURES / "calibration"


def test_embed_calibration_dataset_groups_by_person():
    by_person = embed_calibration_dataset(CALIBRATION_DIR)
    assert set(by_person.keys()) == {"Kit_Harington", "Rose_Leslie"}
    assert len(by_person["Kit_Harington"]) == 2
    assert len(by_person["Rose_Leslie"]) == 2


def test_sample_pairs_counts():
    by_person = embed_calibration_dataset(CALIBRATION_DIR)
    intra, inter = sample_pairs(by_person)
    # 1 intra pair per person (2 photos -> C(2,2)=1), 2 people -> 2 intra pairs
    assert len(intra) == 2
    # 2 x 2 cross pairs between the two people
    assert len(inter) == 4


def test_sample_pairs_scores_in_range_and_intra_higher_on_average():
    by_person = embed_calibration_dataset(CALIBRATION_DIR)
    intra, inter = sample_pairs(by_person)
    assert all(-1.0 <= s <= 1.0 for s in intra + inter)
    assert np.mean(intra) > np.mean(inter)


def test_sample_pairs_caps_inter_class_pairs():
    # Three synthetic people with 2 embeddings each -> 3*C(2,1)*2 = ... just
    # check the cap is respected with a small synthetic set.
    rng = np.random.default_rng(0)
    by_person = {
        "a": [rng.normal(size=128) for _ in range(2)],
        "b": [rng.normal(size=128) for _ in range(2)],
        "c": [rng.normal(size=128) for _ in range(2)],
    }
    intra, inter = sample_pairs(by_person, max_inter_class_pairs=3)
    assert len(intra) == 3  # one pair per person
    assert len(inter) == 3  # capped


def test_compute_eer_threshold_on_synthetic_distributions():
    # Intra scores cluster high, inter scores cluster low, with a clean gap.
    intra_scores = [0.9, 0.85, 0.95]
    inter_scores = [0.1, 0.15, 0.05]
    eer = compute_eer_threshold(intra_scores, inter_scores)
    # With a clean separation, the EER point achieves perfect separation:
    # zero false accepts and zero false rejects.
    assert 0.15 < eer <= 0.85
    far = np.mean(np.array(inter_scores) >= eer)
    frr = np.mean(np.array(intra_scores) < eer)
    assert far == 0.0
    assert frr == 0.0


def test_compute_eer_threshold_known_crossing_point():
    # Symmetric distributions crossing at a known point.
    intra_scores = [0.4, 0.5, 0.6, 0.7]  # 25% below 0.5 -> FRR(0.5) = 0.25
    inter_scores = [0.3, 0.4, 0.5, 0.6]  # 50% >= 0.5 -> FAR(0.5) = 0.5
    # FRR(0.6)=0.5 (2/4 below 0.6), FAR(0.6)=0.25 (1/4 >= 0.6) -> gap smaller at 0.6? check both
    eer = compute_eer_threshold(intra_scores, inter_scores)
    far = np.mean(np.array(inter_scores) >= eer)
    frr = np.mean(np.array(intra_scores) < eer)
    assert abs(far - frr) <= 0.26  # best achievable gap on this small discrete set


def test_compute_far_threshold_known_percentile():
    # 100 inter-class scores, evenly spaced 0.00..0.99; 1% FAR -> top 1 score.
    inter_scores = [i / 100 for i in range(100)]
    threshold = compute_far_threshold(inter_scores, target_far=0.01)
    assert threshold == pytest.approx(0.99)
    far = np.mean(np.array(inter_scores) >= threshold)
    assert far == pytest.approx(0.01)


def test_compute_thresholds_high_at_least_as_strict_as_low_on_fixture_set():
    by_person = embed_calibration_dataset(CALIBRATION_DIR)
    intra, inter = sample_pairs(by_person)
    low, high = compute_thresholds(intra, inter)
    assert high >= low
