"""The matching pipeline shared by the CLI (match.py) and the web UI (app.py):
read calibrated thresholds, embed a query face, rank it against a dataset
index, and label each candidate HIGH_CONFIDENCE / LOW_CONFIDENCE / NO_MATCH.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from face_pipeline.embedder import detect_and_align, embed_face
from face_pipeline.index import DatasetIndex, IndexEntry, rank_matches

HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
NO_MATCH = "NO_MATCH"

LabeledResult = Tuple[IndexEntry, float, str]


@dataclass
class QueryFace:
    embedding: np.ndarray  # (EMBEDDING_SIZE,), not normalized
    aligned_face: np.ndarray  # 112x112 BGR crop the embedding was computed from


@dataclass
class MatchResult:
    query: QueryFace
    labeled: List[LabeledResult]  # most similar first


def load_thresholds(config_path: Path) -> Tuple[Optional[float], Optional[float]]:
    """Return ``(threshold_low, threshold_high)`` from a calibrate.py config.json.

    A missing or unreadable file, or a missing key, gives ``None`` for that value.
    """
    if not config_path.exists():
        return None, None
    try:
        payload = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None, None
    return payload.get("threshold_low"), payload.get("threshold_high")


def classify(score: float, threshold_low: float, threshold_high: float) -> str:
    if score >= threshold_high:
        return HIGH_CONFIDENCE
    if score >= threshold_low:
        return LOW_CONFIDENCE
    return NO_MATCH


def embed_query(image: np.ndarray) -> QueryFace:
    """Detect, align and embed the query face.

    Raises ``NoFaceDetectedError`` if no face is detected.
    """
    aligned = detect_and_align(image)
    return QueryFace(embedding=embed_face(aligned), aligned_face=aligned)


def label_results(
    ranked: List[Tuple[IndexEntry, float]], threshold_low: float, threshold_high: float
) -> List[LabeledResult]:
    return [
        (entry, score, classify(score, threshold_low, threshold_high))
        for entry, score in ranked
    ]


def match_image(
    image: np.ndarray, index: DatasetIndex, threshold_low: float, threshold_high: float
) -> MatchResult:
    """Embed the face in ``image`` and rank and label every indexed candidate.

    Raises ``NoFaceDetectedError`` if no face is detected.
    """
    query = embed_query(image)
    ranked = rank_matches(index, query.embedding)
    return MatchResult(query=query, labeled=label_results(ranked, threshold_low, threshold_high))
