"""Tests for face_pipeline.matching, the pipeline shared by match.py and app.py."""

import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

from face_pipeline.embedder import NoFaceDetectedError
from face_pipeline.index import get_or_build_index
from face_pipeline.matching import (
    HIGH_CONFIDENCE,
    LOW_CONFIDENCE,
    NO_MATCH,
    classify,
    embed_query,
    load_thresholds,
    match_image,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_thresholds_missing_file_gives_none(tmp_path):
    assert load_thresholds(tmp_path / "config.json") == (None, None)


def test_load_thresholds_broken_file_gives_none(tmp_path):
    config = tmp_path / "config.json"
    config.write_text("{not json")
    assert load_thresholds(config) == (None, None)


def test_load_thresholds_reads_both_values(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"threshold_low": 0.1864, "threshold_high": 0.3643}))
    assert load_thresholds(config) == (0.1864, 0.3643)


def test_classify_boundaries_are_at_or_above():
    assert classify(0.4, 0.2, 0.4) == HIGH_CONFIDENCE
    assert classify(0.3999, 0.2, 0.4) == LOW_CONFIDENCE
    assert classify(0.2, 0.2, 0.4) == LOW_CONFIDENCE
    assert classify(0.1999, 0.2, 0.4) == NO_MATCH


def test_match_image_ranks_same_person_first_and_returns_crop(tmp_path):
    dataset_dir = tmp_path / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset_dir)
    index = get_or_build_index(dataset_dir)
    query = cv2.imread(str(FIXTURES / "obama_query.jpg"))

    result = match_image(query, index, 0.2, 0.4)

    people = [entry.person for entry, _, _ in result.labeled]
    assert people[0] == "Barack_Obama"
    assert people.index("Barack_Obama") < people.index("Joe_Biden")
    scores = [score for _, score, _ in result.labeled]
    assert scores == sorted(scores, reverse=True)
    assert [label for _, _, label in result.labeled] == [
        classify(score, 0.2, 0.4) for score in scores
    ]
    assert result.query.aligned_face.shape == (112, 112, 3)
    assert result.query.embedding.shape == (512,)


def test_embed_query_without_a_face_raises():
    blank = np.full((300, 300, 3), 255, dtype=np.uint8)
    with pytest.raises(NoFaceDetectedError):
        embed_query(blank)
