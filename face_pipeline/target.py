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


def ring(threshold: float, steps: int = 180) -> Tuple[np.ndarray, np.ndarray]:
    """The circle of radius ``1 - threshold``, closed (first point repeated)."""
    angles = np.linspace(0.0, 2 * math.pi, steps + 1)
    radius = 1.0 - threshold
    return radius * np.sin(angles), radius * np.cos(angles)
