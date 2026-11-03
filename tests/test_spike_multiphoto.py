"""Tests for the pure parts of spike_multiphoto.py (no network, no models)."""

import numpy as np
import pytest

import spike_multiphoto as spike


def _unit(*values):
    v = np.array(values, dtype=np.float64)
    return v / np.linalg.norm(v)


# Person A has a photo facing the query and one that does not; B has one in between.
QUERY = _unit(1, 0, 0)
A_GOOD, A_BAD = _unit(1, 0.2, 0), _unit(0, 1, 0)
B = _unit(1, 1, 0)
PHOTOS = [np.array([A_BAD, A_GOOD]), np.array([B])]


def _scores(arm, photos=PHOTOS):
    return spike.person_scores(QUERY[None, :], photos, arm)[0]


def test_one_photo_uses_only_the_pool_photo():
    assert _scores("one") == pytest.approx([A_BAD @ QUERY, B @ QUERY])


def test_best_photo_takes_the_highest_of_a_persons_photos():
    assert _scores("best") == pytest.approx([A_GOOD @ QUERY, B @ QUERY])


def test_averaged_compares_with_the_normalised_mean():
    mean = _unit(*(A_BAD + A_GOOD))
    assert _scores("averaged") == pytest.approx([mean @ QUERY, B @ QUERY])


def test_averaging_a_single_photo_changes_nothing():
    assert _scores("averaged", [np.array([B])]) == pytest.approx([B @ QUERY])


def test_top_10_only_gives_extra_chances_to_the_top_faces_alone():
    # Person 0 is outside the top 1 on one photo, so its better photo is not used.
    assert spike.person_scores(QUERY[None, :], PHOTOS, "top", top=1)[0] == pytest.approx([A_BAD @ QUERY, B @ QUERY])
    # With room for both, it is.
    assert spike.person_scores(QUERY[None, :], PHOTOS, "top", top=2)[0] == pytest.approx([A_GOOD @ QUERY, B @ QUERY])


def test_varied_pick_prefers_photos_unlike_those_already_chosen():
    anchor = _unit(1, 0, 0)
    near, near_too, far = _unit(1, 0.05, 0), _unit(1, 0.06, 0), _unit(1, 2, 0)
    candidates = np.array([near, near_too, far])
    assert spike.pick_varied(anchor, candidates, keep=1) == [2]
    assert spike.pick_varied(anchor, candidates, keep=2)[0] == 2
    assert sorted(spike.pick_varied(anchor, candidates, keep=9)) == [0, 1, 2]
    assert spike.pick_varied(anchor, np.empty((0, 3)), keep=3) == []


# A line of faces leading towards the query: 0 -> 1 -> 2 -> 3, with 3 the closest.
LINE = np.array([_unit(1, c, 0) for c in (3.0, 2.0, 1.0, 0.1)])
LINE_LINKS = np.array([[1, 1], [0, 2], [1, 3], [2, 2]])
Q_LINE = _unit(1, 0, 0)


def test_walk_moves_to_better_faces_until_none_is_better():
    result = spike.walk(Q_LINE, 0, LINE, LINE_LINKS, max_steps=10)
    assert result.end == 3
    assert result.steps == 3
    assert result.score == pytest.approx(LINE[3] @ Q_LINE)


def test_walk_stops_at_the_step_limit():
    result = spike.walk(Q_LINE, 0, LINE, LINE_LINKS, max_steps=1)
    assert (result.end, result.steps) == (1, 1)


def test_walk_stops_where_no_neighbour_is_better():
    # Face 1 only links to the worse face 0, so the better faces stay out of reach.
    links = np.array([[1, 1], [0, 0], [1, 3], [2, 2]])
    result = spike.walk(Q_LINE, 1, LINE, links, max_steps=10)
    assert (result.end, result.steps) == (1, 0)


def test_walk_counts_each_face_checked_once():
    result = spike.walk(Q_LINE, 0, LINE, LINE_LINKS, max_steps=10)
    assert result.checked == {0, 1, 2, 3}


def test_nearest_neighbours_leaves_out_the_face_itself():
    links = spike.nearest_neighbours(LINE, k=2, chunk=2)
    assert links.shape == (4, 2)
    assert all(i not in row for i, row in enumerate(links))
    assert links[0][0] == 1  # the most similar first


def test_threshold_fit_and_rate_match_how_the_program_decides():
    # 1% of 200 scores: the threshold keeps the top 2 at or above it.
    scores = np.arange(200) / 200
    threshold = spike.fit_threshold(scores)
    assert spike.rate_at_or_above(scores, threshold) <= 0.01


def test_same_person_hit_needs_the_right_person_first_and_above_the_threshold():
    scores = np.array([[0.5, 0.2], [0.5, 0.2], [0.3, 0.2]])
    hits = spike.same_person_hits(scores, truth=[0, 1, 0], threshold=0.4)
    assert hits.tolist() == [True, False, False]
