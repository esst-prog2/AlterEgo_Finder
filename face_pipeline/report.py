"""Renders a self-contained HTML match report (query image + top-ranked
candidates + confidence status), with all images embedded inline as base64
data URIs -- no external asset files, so the report opens correctly
straight from disk.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

from face_pipeline.attribution import credit_for, safe_source_url
from face_pipeline.images import read_image
from face_pipeline.index import IndexEntry

REPORT_TOP_K = 10

# The shared label colours (DESIGN.md): the same green, gold and grey as the
# page, the promo page and the video. They colour a dot; the label text stays ink.
_LABEL_COLORS = {
    "HIGH_CONFIDENCE": "#1a7f37",  # Same person: green
    "LOW_CONFIDENCE": "#d4a72c",  # Alter Ego: gold
    "NO_MATCH": "#8c959f",  # Not You: grey
}

# The shared fonts and logo ship with the project in static/; the report embeds
# them, so it stays one self-contained file.
_STATIC = Path(__file__).resolve().parent.parent / "static"
_FONTS = (("Barlow", 400, "barlow-latin-400-normal.woff2"),
          ("Barlow Condensed", 700, "barlow-condensed-latin-700-normal.woff2"))


def _font_faces() -> str:
    faces = []
    for family, weight, filename in _FONTS:
        path = _STATIC / "fonts" / filename
        if path.is_file():  # without the file the fallback fonts are used
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            faces.append(f'  @font-face {{ font-family: "{family}"; font-weight: {weight}; '
                         f'src: url(data:font/woff2;base64,{data}) format("woff2"); }}')
    return "\n".join(faces)


def _logo_mark() -> str:
    path = _STATIC / "logo-mark.svg"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip().replace(
        "<svg ", '<svg class="mark" aria-hidden="true" ', 1)


def _image_to_data_uri(image: np.ndarray) -> str:
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        raise ValueError("Failed to encode image for report")
    encoded = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _credit_line(credit: Optional[dict]) -> str:
    if not credit:
        return ""
    # Credits are text from strangers: escaped, and linked only to Commons pages.
    text = html.escape(f"Photo: {credit.get('author', '')}, {credit.get('license', '')}")
    url = safe_source_url(credit.get("source", ""))
    link = f' <a href="{html.escape(url, quote=True)}">source</a>' if url else ""
    return f'\n        <div class="candidate-credit">{text}{link}</div>'


def _candidate_card(entry: IndexEntry, score: float, label: str, credit: Optional[dict] = None) -> str:
    image = read_image(entry.filepath)
    data_uri = _image_to_data_uri(image) if image is not None else ""
    color = _LABEL_COLORS.get(label, "#8c959f")
    # Person names are dataset folder names, i.e. untrusted input.
    person = html.escape(entry.person)
    label = html.escape(label)
    return f"""    <div class="candidate">
      <img src="{data_uri}" alt="{person}">
      <div class="candidate-info">
        <div class="candidate-name">{person}</div>
        <div class="candidate-score">{score:.4f}</div>
        <div class="candidate-label"><span class="dot" style="background: {color}"></span>{label}</div>{_credit_line(credit)}
      </div>
    </div>"""


def render_report(
    query_image: Union[Path, np.ndarray],
    results: List[Tuple[IndexEntry, float, str]],
    output_path: Path,
    attribution: Optional[Dict[str, dict]] = None,
) -> None:
    """Render a self-contained HTML report to ``output_path``.

    ``query_image`` is either a path to the query image file or the already
    decoded image (BGR array), as the web UI has it.

    ``results`` is a list of ``(IndexEntry, score, confidence_label)``
    tuples, already ranked most-similar first. Only the top
    ``REPORT_TOP_K`` are included. ``attribution`` holds the dataset's photo
    credits, if it records any (see face_pipeline.attribution).
    """
    if not isinstance(query_image, np.ndarray):
        query_image = read_image(query_image)
    query_data_uri = _image_to_data_uri(query_image) if query_image is not None else ""

    top_results = results[:REPORT_TOP_K]
    candidate_cards = "\n".join(
        _candidate_card(entry, score, label, credit_for(attribution, entry.filepath))
        for entry, score, label in top_results
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AlterEgo Finder - Match Report</title>
<style>
{_font_faces()}
  body {{ font-family: Barlow, system-ui, sans-serif; font-variant-numeric: tabular-nums; color: #1f2328; margin: 0; padding: 2rem;
    background-color: #eef3f8;
    background-image: linear-gradient(rgba(29, 60, 120, 0.09) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(29, 60, 120, 0.09) 1px, transparent 1px);
    background-size: 24px 24px; }}
  header {{ display: flex; align-items: center; gap: 0.8rem; padding-bottom: 0.9rem; border-bottom: 2px solid #1d3c78; margin-bottom: 1.5rem; }}
  header .mark {{ width: 56px; height: 56px; flex: none; }}
  h1 {{ font-family: "Barlow Condensed", "Arial Narrow", sans-serif; font-weight: 700; font-size: 1.9rem; line-height: 0.95;
    text-transform: uppercase; color: #1f2328; margin: 0; }}
  h1 small {{ display: block; font-size: 1.05rem; color: #1d3c78; letter-spacing: 0.03em; }}
  .query {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }}
  .query img {{ width: 140px; height: 140px; object-fit: cover; border: 2px solid #1d3c78; }}
  .query div {{ font-family: "Barlow Condensed", "Arial Narrow", sans-serif; font-weight: 700; text-transform: uppercase; color: #1d3c78; }}
  .candidates {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
  .candidate {{ background: #f8fbfd; border: 2px solid #1d3c78; overflow: hidden; width: 168px; }}
  .candidate img {{ width: 100%; height: 164px; object-fit: cover; display: block; border-bottom: 2px solid #1d3c78; }}
  .candidate-info {{ padding: 0.55rem 0.6rem 0.65rem; }}
  .candidate-name {{ font-weight: 400; font-size: 0.92rem; overflow-wrap: anywhere; }}
  .candidate-score {{ font-family: "Barlow Condensed", "Arial Narrow", sans-serif; font-weight: 700; font-size: 1.15rem; margin-top: 0.15rem; }}
  .candidate-label {{ display: flex; align-items: center; gap: 0.4em; font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
    font-weight: 700; font-size: 0.85rem; letter-spacing: 0.03em; margin-top: 0.2rem; }}
  .dot {{ width: 0.8em; height: 0.8em; border-radius: 50%; border: 1.5px solid #1f2328; flex: none; }}
  .candidate-credit {{ font-size: 0.72rem; color: #46505d; margin-top: 0.35rem; overflow-wrap: anywhere; }}
  .candidate-credit a {{ color: #1d3c78; }}
</style>
</head>
<body>
  <header>{_logo_mark()}<h1>AlterEgo Finder<small>Match report</small></h1></header>
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
    output_path.write_text(page, encoding="utf-8")
