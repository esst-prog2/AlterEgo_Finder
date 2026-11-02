"""Tests for face_pipeline.target, the layout of the web UI's similarity target."""

import math

import numpy as np
import pytest

from face_pipeline.index import IndexEntry
from face_pipeline.target import place_names, ring, target_points


def _labeled(people_scores):
    """Ranked (entry, score, label) tuples, most similar first, as app.py has them."""
    ranked = sorted(people_scores, key=lambda ps: -ps[1])
    return [
        (IndexEntry(person=person, filepath=f"{person}_{i}.jpg"), score, "LABEL")
        for i, (person, score) in enumerate(ranked)
    ]


SCORES = [("A", 0.70), ("B", 0.40), ("A", 0.35), ("C", 0.20), ("D", 0.05), ("E", -0.10)]


def test_radius_is_exactly_one_minus_score_for_every_face():
    points = target_points(_labeled(SCORES), top=3)

    assert len(points) == len(SCORES)
    for p in points:
        assert p.radius == pytest.approx(1 - p.score)
        assert math.hypot(p.x, p.y) == pytest.approx(p.radius)


def test_ring_radius_is_one_minus_threshold():
    xs, ys = ring(0.3643)
    assert np.allclose(np.hypot(xs, ys), 1 - 0.3643)
    xs, ys = ring(-1.0)  # test configs use -1
    assert np.allclose(np.hypot(xs, ys), 2.0)


def test_top_n_by_rank_are_named():
    labeled = _labeled(SCORES)
    points = target_points(labeled, top=3)

    named = {(p.person, p.score) for p in points if p.named}
    assert named == {(e.person, s) for e, s, _ in labeled[:3]}
    assert sum(p.named for p in target_points(labeled, top=50)) == len(SCORES)


def test_named_faces_are_evenly_spaced_over_the_circle():
    points = [p for p in target_points(_labeled(SCORES), top=4) if p.named]

    angles = sorted(p.angle for p in points)
    gaps = np.diff(angles + [angles[0] + 2 * math.pi])
    assert np.allclose(gaps, 2 * math.pi / 4)


def test_photos_of_one_person_sit_side_by_side_among_named():
    # Ranks: A 0.70, B 0.40, A 0.35 -> A's two photos must be adjacent.
    points = [p for p in target_points(_labeled(SCORES), top=3) if p.named]
    order = [p.person for p in sorted(points, key=lambda p: p.angle)]
    assert order == ["A", "A", "B"]


def test_unnamed_faces_spread_evenly_offset_by_half_a_step():
    points = [p for p in target_points(_labeled(SCORES), top=2) if not p.named]

    angles = sorted(p.angle for p in points)
    step = 2 * math.pi / len(points)
    assert angles[0] == pytest.approx(step / 2)
    assert np.allclose(np.diff(angles), step)


def test_identical_photo_sits_at_the_centre():
    points = target_points(_labeled([("Self", 1.0), ("Other", 0.2)]), top=2)
    self_point = next(p for p in points if p.person == "Self")
    assert self_point.radius == pytest.approx(0.0)
    assert (self_point.x, self_point.y) == pytest.approx((0.0, 0.0))


def test_unnamed_faces_are_not_placed_in_rank_order():
    # Rank order around the circle made the faint faces a spiral (radius grows
    # with rank), so the angle quietly encoded rank (screenshot 2026-10-20).
    labeled = _labeled([(f"P{i:02d}", 0.5 - i / 100) for i in range(40)])
    points = [p for p in target_points(labeled, top=5) if not p.named]
    ranks_by_angle = [p.rank for p in sorted(points, key=lambda p: p.angle)]
    assert ranks_by_angle != sorted(ranks_by_angle)
    assert ranks_by_angle != sorted(ranks_by_angle, reverse=True)


# --- where the names go (decided 2026-11-03) -------------------------------------

W, H = 640, 460
NO_LEGEND = (0, 0, 0, 0)


def _places(names, legend=NO_LEGEND):
    return place_names(names, W, H, legend)


def test_a_name_with_nothing_in_its_way_points_outward():
    names = [(420, 200, "#1 Right"), (200, 300, "#2 Left")]
    assert _places(names) == ["right", "left"]


def test_a_name_on_the_vertical_axis_counts_as_right_half():
    assert _places([(W / 2, 100, "#1 Top")]) == ["right"]


def test_a_blocked_name_takes_the_first_free_place_in_order():
    # #2's dot sits on #1's outward place; above is free.
    assert _places([(320, 150, "#1 A long enough name"), (370, 150, "#2 B")])[0] == "above"
    # With a dot above as well, below comes next.
    assert _places([(320, 150, "#1 A long enough name"), (370, 150, "#2 B"), (320, 135, "#3 C")])[0] == "below"
    # With above and below taken too, the inward side is left.
    assert _places([(320, 150, "#1 A long enough name"), (370, 150, "#2 B"), (320, 135, "#3 C"),
                    (320, 165, "#4 D")])[0] == "left"


def test_a_later_name_avoids_names_already_placed():
    # #2's dot pushes #1's name above its dot, where it lies across #3's usual place
    # without touching #3's dot, so only #1's name can move #3's.
    names = [(420, 200, "#1 A name of some length"), (470, 200, "#2 B"), (330, 186, "#3 A long enough name")]
    places = _places(names)
    assert places[0] == "above"
    assert places[2] != "right"


def test_the_legend_and_the_chart_edge_count_as_collisions():
    assert _places([(420, 40, "#1 Name")], legend=(400, 20, 600, 60)) != ["right"]
    # Too long to fit to the right of a dot near the edge.
    assert _places([(600, 200, "#1 A name far too long to fit")]) != ["right"]


def test_with_no_free_place_the_least_overlapping_one_is_taken():
    # Dots crowd every place but the outward one, which only clips the edge a little.
    x = W - 90
    dots = [(x + dx, 150 + dy, "x") for dx in (-45, 0) for dy in (-14, 14)] + [(x - 45, 150, "x")]
    (first, *_) = _places([(x, 150, "#1 A long name")] + dots)
    assert first == "right"


def test_placement_is_deterministic_and_answers_every_name():
    names = [(320 + 5 * i, 150 + 3 * i, f"#{i + 1} Name {i}") for i in range(20)]
    assert _places(names) == _places(names)
    assert len(_places(names)) == 20
