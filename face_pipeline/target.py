"""Layout of the web UI's similarity target: the query at the centre and every
indexed face at a distance of exactly ``1 - score`` from it.

Only the distance carries information. A 2D projection of the 512-d space
would misplace the true neighbours (PLANNING_LOG.md, 2026-10-20), so the
angle is just a way to spread the faces out: the top N in one evenly spaced
pass in rank order (clockwise from 12 o'clock, so they read #1, #2, ...), the
rest in a second pass offset by half a step in a fixed scrambled order. Rank
order there would turn the cloud into a spiral, since distance grows with
rank. In both passes, photos of one person sit side by side.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from face_pipeline.matching import LabeledResult

Box = Tuple[float, float, float, float]  # left, top, right, bottom


# Sizes on the chart, in pixels. Text is drawn in the browser, so its width is an
# estimate: the pool's names at font size 12 measured 5.9 px per character in
# Chromium, and 11 px tall. A dot's radius is 6.4.
CHAR_PX = 6
LINE_PX = 12
DOT_PX = 6.5  # half the side of the box around a named face's dot
_BESIDE, _ABOVE = 9, 14  # from a dot's centre to a name's near end, or its middle line

# Where a name can go relative to its dot: (align, dx, dy), as Vega draws them.
NAME_PLACES = {
    "right": ("left", _BESIDE, 0),
    "left": ("right", -_BESIDE, 0),
    "above": ("center", 0, -_ABOVE),
    "below": ("center", 0, _ABOVE),
    "above right": ("left", 0, -_ABOVE),
    "above left": ("right", 0, -_ABOVE),
    "below right": ("left", 0, _ABOVE),
    "below left": ("right", 0, _ABOVE),
}


@dataclass(frozen=True)
class TargetPoint:
    person: str
    filepath: str  # the matched image, for the tooltip thumbnail
    score: float
    label: str
    rank: int  # 1 = most similar
    named: bool  # one of the top N
    radius: float  # exactly 1 - score
    angle: float  # radians, clockwise from 12 o'clock; carries no meaning
    x: float
    y: float


def _grouped_by_person(
    items: List[Tuple[int, LabeledResult]], scrambled: bool
) -> List[Tuple[int, LabeledResult]]:
    """Order a person's photos consecutively, people by best rank or, if
    ``scrambled``, by a fixed hash of their name."""
    best_rank: Dict[str, int] = {}
    for rank, (entry, _, _) in items:
        best_rank.setdefault(entry.person, rank)

    def person_key(person: str) -> int:
        return zlib.crc32(person.encode("utf-8")) if scrambled else best_rank[person]

    return sorted(items, key=lambda item: (person_key(item[1][0].person), item[1][0].person, item[0]))


def _spread(items, named: bool, offset: float) -> List[TargetPoint]:
    points = []
    step = 2 * math.pi / len(items) if items else 0.0
    for i, (rank, (entry, score, label)) in enumerate(_grouped_by_person(items, scrambled=not named)):
        radius = 1.0 - score
        angle = offset * step + i * step
        points.append(TargetPoint(
            person=entry.person, filepath=str(entry.filepath), score=score, label=label, rank=rank, named=named,
            radius=radius, angle=angle,
            x=radius * math.sin(angle), y=radius * math.cos(angle),
        ))
    return points


def target_points(labeled: List[LabeledResult], top: int) -> List[TargetPoint]:
    """One point per entry of ``labeled`` (ranked, most similar first); the
    first ``top`` are named."""
    ranked = list(enumerate(labeled, start=1))
    return _spread(ranked[:top], named=True, offset=0.0) + _spread(
        ranked[top:], named=False, offset=0.5
    )


def _name_box(x: float, y: float, text: str, place: str) -> Box:
    align, dx, dy = NAME_PLACES[place]
    width = len(text) * CHAR_PX
    left = x + dx - {"left": 0, "center": width / 2, "right": width}[align]
    return left, y + dy - LINE_PX / 2, left + width, y + dy + LINE_PX / 2


SHIFTED_PLACES = ("above right", "above left", "below right", "below left")


def _overlap(a: Box, b: Box) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def place_names(names: List[Tuple[float, float, str]], width: float, height: float, legend: Box) -> List[str]:
    """Where each name goes relative to its dot: a key of ``NAME_PLACES``.

    ``names`` are (x, y, text) in chart pixels, in rank order, so the top faces get
    first choice. A name points outward from the centre unless that collides with
    another name, a named face's dot, ``legend`` or the chart's edge; then it takes
    the first free place of above, below, inward and the four shifted sideways, or
    the one overlapping least.
    """
    dots = [(x - DOT_PX, y - DOT_PX, x + DOT_PX, y + DOT_PX) for x, y, _ in names]
    chart: Box = (0.0, 0.0, width, height)
    placed: List[Box] = []
    places = []
    for i, (x, y, text) in enumerate(names):
        outward, inward = ("right", "left") if x >= width / 2 else ("left", "right")

        def collisions(place: str) -> float:
            box = _name_box(x, y, text, place)
            off_chart = (box[2] - box[0]) * (box[3] - box[1]) - _overlap(box, chart)
            others = dots[:i] + dots[i + 1:] + placed + [legend]
            return off_chart + sum(_overlap(box, other) for other in others)

        # min keeps the first of equals, so the first free place wins.
        place = min((outward, "above", "below", inward, *SHIFTED_PLACES), key=collisions)
        places.append(place)
        placed.append(_name_box(x, y, text, place))
    return places


def ring(threshold: float, steps: int = 180) -> Tuple[np.ndarray, np.ndarray]:
    """The circle of radius ``1 - threshold``, closed (first point repeated)."""
    angles = np.linspace(0.0, 2 * math.pi, steps + 1)
    radius = 1.0 - threshold
    return radius * np.sin(angles), radius * np.cos(angles)
