import math

import numpy as np

from face_pipeline.index import DatasetIndex, IndexEntry, rank_matches


def _unit(vec):
    vec = np.array(vec, dtype=np.float32)
    return vec / np.linalg.norm(vec)


def test_rank_matches_against_hand_computed_cosine_similarity():
    # Two orthogonal-ish candidates and one identical-to-query candidate.
    entry_same = IndexEntry(person="Same", filepath="same.jpg")
    entry_orth = IndexEntry(person="Orthogonal", filepath="orth.jpg")
    entry_opposite = IndexEntry(person="Opposite", filepath="opp.jpg")

    query = _unit([1.0, 0.0, 0.0])
    same = _unit([1.0, 0.0, 0.0])
    orthogonal = _unit([0.0, 1.0, 0.0])
    opposite = _unit([-1.0, 0.0, 0.0])

    embeddings = np.stack([same, orthogonal, opposite])
    index = DatasetIndex(
        embeddings=embeddings, entries=[entry_same, entry_orth, entry_opposite]
    )

    results = rank_matches(index, query)

    # Hand-computed cosine similarities: same=1.0, orthogonal=0.0, opposite=-1.0
    assert [e.person for e, _ in results] == ["Same", "Orthogonal", "Opposite"]
    scores = {e.person: score for e, score in results}
    assert math.isclose(scores["Same"], 1.0, abs_tol=1e-6)
    assert math.isclose(scores["Orthogonal"], 0.0, abs_tol=1e-6)
    assert math.isclose(scores["Opposite"], -1.0, abs_tol=1e-6)


def test_rank_matches_handles_empty_index():
    index = DatasetIndex(embeddings=np.empty((0, 3), dtype=np.float32), entries=[])
    assert rank_matches(index, _unit([1.0, 0.0, 0.0])) == []
