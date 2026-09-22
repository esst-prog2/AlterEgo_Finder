"""Renders a self-contained HTML match report (query image + top-ranked
candidates + confidence status), with all images embedded inline as base64
data URIs -- no external asset files, so the report opens correctly
straight from disk.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from face_pipeline.index import IndexEntry

REPORT_TOP_K = 10

_LABEL_COLORS = {
    "HIGH_CONFIDENCE": "#1a7f37",  # green
    "LOW_CONFIDENCE": "#9a6700",  # amber
    "NO_MATCH": "#57606a",  # gray
}


def _image_to_data_uri(image: np.ndarray) -> str:
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        raise ValueError("Failed to encode image for report")
    encoded = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _candidate_card(entry: IndexEntry, score: float, label: str) -> str:
    image = cv2.imread(str(entry.filepath))
    data_uri = _image_to_data_uri(image) if image is not None else ""
    color = _LABEL_COLORS.get(label, "#57606a")
    return f"""    <div class="candidate">
      <img src="{data_uri}" alt="{entry.person}">
      <div class="candidate-info">
        <div class="candidate-name">{entry.person}</div>
        <div class="candidate-score">{score:.4f}</div>
        <div class="candidate-label" style="color: {color}">{label}</div>
      </div>
    </div>"""


def render_report(
    query_image_path: Path,
    results: List[Tuple[IndexEntry, float, str]],
    output_path: Path,
) -> None:
    """Render a self-contained HTML report to ``output_path``.

    ``results`` is a list of ``(IndexEntry, score, confidence_label)``
    tuples, already ranked most-similar first. Only the top
    ``REPORT_TOP_K`` are included.
    """
    query_image = cv2.imread(str(query_image_path))
    query_data_uri = _image_to_data_uri(query_image) if query_image is not None else ""

    top_results = results[:REPORT_TOP_K]
    candidate_cards = "\n".join(
        _candidate_card(entry, score, label) for entry, score, label in top_results
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AlterEgo Finder - Match Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #f6f8fa; color: #1f2328; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.25rem; }}
  .query {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }}
  .query img {{ width: 140px; height: 140px; object-fit: cover; border-radius: 8px; }}
  .candidates {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
  .candidate {{ background: white; border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; width: 160px; }}
  .candidate img {{ width: 100%; height: 160px; object-fit: cover; display: block; }}
  .candidate-info {{ padding: 0.5rem; }}
  .candidate-name {{ font-weight: 600; font-size: 0.9rem; }}
  .candidate-score {{ font-size: 0.8rem; color: #57606a; }}
  .candidate-label {{ font-size: 0.8rem; font-weight: 700; margin-top: 0.25rem; }}
</style>
</head>
<body>
  <h1>AlterEgo Finder - Match Report</h1>
  <div class="query">
    <img src="{query_data_uri}" alt="query image">
    <div>Query image</div>
  </div>
  <div class="candidates">
{candidate_cards}
  </div>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
