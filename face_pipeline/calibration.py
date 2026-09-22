"""Threshold calibration: pair sampling, similarity scoring, EER and
false-accept-rate (FAR) based threshold search.

Two thresholds are derived from one calibration run:
  - the low threshold, at the equal-error-rate (EER) point
    (intra-class false-reject rate == inter-class false-accept rate);
  - the high threshold, at a low false-accept-rate operating point on the
    inter-class distribution (see HIGH_THRESHOLD_FAR).
"""

from __future__ import annotations

import itertools
import random
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

from face_pipeline.embedder import NoFaceDetectedError, extract_embedding

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

MAX_INTER_CLASS_PAIRS = 5000
HIGH_THRESHOLD_FAR = 0.01  # 1% false-accept-rate operating point
SAMPLING_SEED = 0


def _iter_people(calibration_dir: Path):
    for person_dir in sorted(p for p in calibration_dir.iterdir() if p.is_dir()):
        images = [
            p
            for p in sorted(person_dir.iterdir())
            if p.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if images:
            yield person_dir.name, images


def embed_calibration_dataset(calibration_dir: Path) -> Dict[str, List[np.ndarray]]:
    """Extract embeddings for every image under ``calibration_dir``, grouped by person.

    Images with no detectable face are skipped.
    """
    by_person: Dict[str, List[np.ndarray]] = {}
    for person, image_paths in _iter_people(calibration_dir):
        embeddings = []
        for image_path in image_paths:
            image = cv2.imread(str(image_path))
            if image is None:
                continue
            try:
                embeddings.append(extract_embedding(image))
            except NoFaceDetectedError:
                continue
        if embeddings:
            by_person[person] = embeddings
    return by_person


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def sample_pairs(
    by_person: Dict[str, List[np.ndarray]],
    max_inter_class_pairs: int = MAX_INTER_CLASS_PAIRS,
    seed: int = SAMPLING_SEED,
) -> Tuple[List[float], List[float]]:
    """Return ``(intra_class_scores, inter_class_scores)``.

    All same-person pairs are used. Different-person pairs are capped at
    ``max_inter_class_pairs``, sampled uniformly at random when exceeded.
    """
    intra_scores: List[float] = []
    for embeddings in by_person.values():
        for a, b in itertools.combinations(embeddings, 2):
            intra_scores.append(_cosine(a, b))

    inter_pairs: List[Tuple[np.ndarray, np.ndarray]] = []
    people = list(by_person.keys())
    for i in range(len(people)):
        for j in range(i + 1, len(people)):
            for a in by_person[people[i]]:
                for b in by_person[people[j]]:
                    inter_pairs.append((a, b))

    if len(inter_pairs) > max_inter_class_pairs:
        rng = random.Random(seed)
        inter_pairs = rng.sample(inter_pairs, max_inter_class_pairs)

    inter_scores = [_cosine(a, b) for a, b in inter_pairs]
    return intra_scores, inter_scores


def compute_eer_threshold(intra_scores: List[float], inter_scores: List[float]) -> float:
    """Return the similarity score where FRR (intra-class) equals FAR (inter-class)."""
    intra = np.array(intra_scores, dtype=np.float64)
    inter = np.array(inter_scores, dtype=np.float64)
    candidates = sorted(set(intra_scores) | set(inter_scores))

    best_threshold = candidates[0]
    best_gap = float("inf")
    for t in candidates:
        far = float(np.mean(inter >= t)) if inter.size else 0.0
        frr = float(np.mean(intra < t)) if intra.size else 0.0
        gap = abs(far - frr)
        if gap < best_gap:
            best_gap = gap
            best_threshold = t
    return best_threshold


def compute_far_threshold(
    inter_scores: List[float], target_far: float = HIGH_THRESHOLD_FAR
) -> float:
    """Return the lowest score at or above which at most ``target_far`` of the
    inter-class scores fall (the strictest achievable estimate when there
    isn't enough data to resolve the exact percentile).
    """
    inter = np.array(sorted(inter_scores), dtype=np.float64)
    if inter.size == 0:
        return 1.0
    index = int(np.ceil((1 - target_far) * inter.size))
    index = min(max(index, 0), inter.size - 1)
    return float(inter[index])


def compute_thresholds(
    intra_scores: List[float], inter_scores: List[float]
) -> Tuple[float, float]:
    """Return ``(threshold_low, threshold_high)``.

    ``threshold_high`` is clamped to be at least ``threshold_low``, since a
    very small calibration set can otherwise make the FAR-based estimate
    unstable relative to the EER point.
    """
    low = compute_eer_threshold(intra_scores, inter_scores)
    high = compute_far_threshold(inter_scores)
    return low, max(high, low)
