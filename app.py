"""Web UI: drop a face photo, pick an indexed dataset, and see the top
candidates with similarity scores and calibrated confidence labels.

Run from the repository root (so .streamlit/config.toml applies and the page
is served on localhost only):

    pip install -r requirements-ui.txt
    streamlit run app.py
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import streamlit as st

from face_pipeline.embedder import NoFaceDetectedError
from face_pipeline.index import CACHE_DIRNAME, EMBEDDINGS_FILENAME, get_or_build_index, rank_matches
from face_pipeline.matching import (
    HIGH_CONFIDENCE,
    LOW_CONFIDENCE,
    NO_MATCH,
    QueryFace,
    embed_query,
    label_results,
    load_thresholds,
)
from face_pipeline.report import REPORT_TOP_K, render_report
from face_pipeline.target import ring, target_points

MAX_CANDIDATES = 20
CARDS_PER_ROW = 5
_LABEL_COLORS = {HIGH_CONFIDENCE: "green", LOW_CONFIDENCE: "orange"}  # NO_MATCH: gray
# The page shows only these plain names. The technical labels are for the
# developers: they stay in the CLI, the HTML report and the specs.
PLAIN_NAMES = {HIGH_CONFIDENCE: "Same person", LOW_CONFIDENCE: "Alter Ego", NO_MATCH: "Not You"}
THUMBNAIL_PX = 128  # longest side of the tooltip face thumbnails (top N only)
# Wider than tall, so names beside the outer dots fit; the x range is scaled
# by the same ratio, so one unit is as many pixels across as up and the rings
# stay round.
TARGET_WIDTH, TARGET_HEIGHT = 640, 460
TARGET_RAYS = 5  # top faces that get a guide ray from the centre
_TARGET_COLORS = {"domain": [PLAIN_NAMES[HIGH_CONFIDENCE], PLAIN_NAMES[LOW_CONFIDENCE],
                             PLAIN_NAMES[NO_MATCH]],
                  "range": ["#1a7f37", "#d4a72c", "#8c959f"]}
# Target colours per page theme (st.context.theme.type). "ink" is the centre
# and the names, "muted" the ring labels and rays, "faint" the rings and the
# unnamed faces. None (theme not reported yet) uses one gray that reads on both.
_TARGET_PALETTES = {
    "light": {"ink": "#1f2328", "muted": "#57606a", "faint": "#8c959f"},
    "dark": {"ink": "#f0f6fc", "muted": "#9198a1", "faint": "#6e7681"},
    None: {"ink": "#8c959f", "muted": "#8c959f", "faint": "#8c959f"},
}


def _data_dir() -> Path:
    # Overridable so tests can point the page at a temporary data/ folder.
    default = Path(__file__).resolve().parent / "data"
    return Path(os.environ.get("ALTEREGO_DATA_DIR", default))


def list_datasets(data_dir: Path) -> List[Path]:
    """Folders directly under ``data_dir`` that already have an embedding index.

    Unindexed folders (e.g. data/lfw/, data/results/) are left out, so the page
    never starts a long index build from a wrong pick.
    """
    if not data_dir.is_dir():
        return []
    return sorted(
        p for p in data_dir.iterdir()
        if p.is_dir() and (p / CACHE_DIRNAME / EMBEDDINGS_FILENAME).exists()
    )


def decode_image(image_bytes: bytes) -> Optional[np.ndarray]:
    return cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)


@st.cache_data(show_spinner="Finding the face...", max_entries=8)
def _embed_upload(image_bytes: bytes) -> Optional[QueryFace]:
    """The query face of an uploaded photo, or None if it has no face.

    Cached on the bytes, so moving a slider or switching dataset does not
    re-run detection and embedding.
    """
    try:
        return embed_query(decode_image(image_bytes))
    except NoFaceDetectedError:
        return None


def _threshold_slider(dataset: Path, low: float, high: float):
    selected = st.sidebar.slider(
        "Thresholds (low, high)",
        min_value=min(0.0, low),
        max_value=max(1.0, high),
        value=(low, high),
        step=0.0001,
        format="%.4f",
        # One key per dataset: switching dataset starts from its calibrated values.
        key=f"thresholds::{dataset.name}",
        help=(f"Below low: {PLAIN_NAMES[NO_MATCH]}. From low: {PLAIN_NAMES[LOW_CONFIDENCE]}. "
              f"From high: {PLAIN_NAMES[HIGH_CONFIDENCE]}."),
    )
    if (round(selected[0], 4), round(selected[1], 4)) != (round(low, 4), round(high, 4)):
        st.sidebar.warning(
            f"Thresholds overridden: the calibrated values are low {low:.4f}, high {high:.4f}."
        )
    return selected


def _square_crop(image: np.ndarray) -> np.ndarray:
    """The centred square of ``image``, so every card picture has the same shape."""
    height, width = image.shape[:2]
    side = min(height, width)
    top, left = (height - side) // 2, (width - side) // 2
    return image[top: top + side, left: left + side]


def _show_cards(labeled, top: int) -> None:
    shown = labeled[:top]
    for row_start in range(0, len(shown), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW)
        for offset, (entry, score, label) in enumerate(shown[row_start: row_start + CARDS_PER_ROW]):
            with columns[offset]:
                image = cv2.imread(str(entry.filepath))
                if image is not None:
                    st.image(_square_crop(image), channels="BGR", width="stretch")
                # Person names are dataset folder names, i.e. untrusted input:
                # st.text shows them literally, with no Markdown or HTML.
                st.text(f"#{row_start + offset + 1} {entry.person}")
                color = _LABEL_COLORS.get(label, "gray")
                st.markdown(f"`{score:.4f}` :{color}[**{PLAIN_NAMES[label]}**]")


@st.cache_data(show_spinner=False, max_entries=1024)
def _thumbnail(path: str) -> str:
    """A small JPEG data URI of the image at ``path``, or "" if unreadable."""
    image = cv2.imread(path)
    if image is None:
        return ""
    height, width = image.shape[:2]
    scale = THUMBNAIL_PX / max(height, width)
    small = cv2.resize(image, (max(1, round(width * scale)), max(1, round(height * scale))),
                       interpolation=cv2.INTER_AREA)
    ok, buffer = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("ascii") if ok else ""


def _target_spec(labeled, top: int, low: float, high: float, theme: Optional[str] = None) -> dict:
    """Vega-Lite spec of the similarity target (layout: face_pipeline/target.py).

    Every layer carries its own inline data. Streamlit sends DataFrames and
    top-level chart data through pyarrow, which Windows' application control
    blocks on some machines; inline layer data is passed through as JSON.
    """
    colors = _TARGET_PALETTES.get(theme, _TARGET_PALETTES[None])
    points = target_points(labeled, top)
    reach = max([p.radius for p in points] + [1.0 - low, 1.0 - high])
    half_y = 1.45 * reach  # headroom above the circle for the three legend lines
    half_x = half_y * TARGET_WIDTH / TARGET_HEIGHT
    x_scale = {"domain": [-half_x, half_x]}
    y_scale = {"domain": [-half_y, half_y]}
    xy = {
        "x": {"field": "x", "type": "quantitative", "scale": x_scale, "axis": None},
        "y": {"field": "y", "type": "quantitative", "scale": y_scale, "axis": None},
    }
    tooltip = [
        {"field": "person", "type": "nominal", "title": "Person"},
        {"field": "score", "type": "quantitative", "title": "Score", "format": ".4f"},
        {"field": "distance", "type": "quantitative", "title": "Distance (1 - score)", "format": ".4f"},
        {"field": "zone", "type": "nominal", "title": "Label"},
    ]
    # vega-tooltip shows a field titled "image" as a picture; only the named
    # faces carry one, so the chart stays small (all ~505 would add MBs).
    named_tooltip = tooltip + [{"field": "image", "title": "image"}]
    # Rays run from (x0, y0) = the centre to the face, all as plain data fields.
    origin = {"x": {"field": "x0", "type": "quantitative", "scale": x_scale, "axis": None},
              "y": {"field": "y0", "type": "quantitative", "scale": y_scale, "axis": None},
              "x2": {"field": "x"}, "y2": {"field": "y"}}

    def faces(named: bool):
        rows = []
        for p in points:
            if p.named != named:
                continue
            row = {"x": p.x, "y": p.y, "person": p.person, "score": p.score,
                   "distance": p.radius, "zone": PLAIN_NAMES[p.label],
                   "named": p.named, "rank": p.rank}
            if named and (thumbnail := _thumbnail(p.filepath)):
                row["image"] = thumbnail
            rows.append(row)
        return rows

    layers = []
    layers.append({
        "data": {"values": [{"x0": 0.0, "y0": 0.0, "x": p.x, "y": p.y, "rank": p.rank}
                            for p in points if p.rank <= min(TARGET_RAYS, top)]},
        "mark": {"type": "rule", "strokeDash": [2, 3], "strokeWidth": 1,
                 "color": colors["muted"], "opacity": 0.5},
        "encoding": origin,
    })
    # The rings are explained by a legend in the top-left corner, above the
    # circle: labels on the rings themselves collided with named faces.
    legend = (
        f"inside inner ring (high {high:.4f}): {PLAIN_NAMES[HIGH_CONFIDENCE]}",
        f"between rings (low {low:.4f}): {PLAIN_NAMES[LOW_CONFIDENCE]}",
        f"outside: {PLAIN_NAMES[NO_MATCH]}",
    )
    for row, text in enumerate(legend):
        layers.append({
            "data": {"values": [{"x": -0.97 * half_x, "y": (0.95 - 0.075 * row) * half_y}]},
            "mark": {"type": "text", "text": text, "align": "left", "baseline": "middle",
                     "fontSize": 12, "color": colors["muted"]},
            "encoding": xy,
        })
    for threshold in (low, high):
        xs, ys = ring(threshold)
        layers.append({
            "data": {"values": [{"x": x, "y": y, "i": i} for i, (x, y) in enumerate(zip(xs, ys))]},
            "mark": {"type": "line", "strokeDash": [4, 4], "color": colors["faint"]},
            "encoding": {**xy, "order": {"field": "i", "type": "quantitative"}},
        })
    layers.append({
        "data": {"values": faces(named=False)},
        "mark": {"type": "circle", "size": 22, "opacity": 0.3, "color": colors["faint"]},
        "encoding": {**xy, "tooltip": tooltip},
    })
    layers.append({
        "data": {"values": faces(named=True)},
        "mark": {"type": "circle", "size": 130, "opacity": 0.95},
        "encoding": {**xy, "tooltip": named_tooltip,
                     "color": {"field": "zone", "type": "nominal",
                               "scale": _TARGET_COLORS, "legend": None}},
    })
    # Names sit beside their dot, pointing outward (left-aligned on the right
    # half, right-aligned on the left), so neighbours do not run into each
    # other. They go through Vega's SVG text, which does not interpret HTML.
    for right_half, align, dx in ((True, "left", 9), (False, "right", -9)):
        layers.append({
            "data": {"values": [{"x": p.x, "y": p.y,
                                 "text": f"#{p.rank} {p.person}"
                                         + (f" ({p.score:.4f})" if p.rank == 1 else "")}
                                for p in points if p.named and (p.x >= 0) == right_half]},
            "mark": {"type": "text", "align": align, "dx": dx, "baseline": "middle",
                     "fontSize": 12, "color": colors["ink"]},
            "encoding": {**xy, "text": {"field": "text", "type": "nominal"}},
        })
    layers.append({
        "data": {"values": [{"x": 0.0, "y": 0.0}]},
        "mark": {"type": "point", "shape": "cross", "filled": True, "size": 260, "color": colors["ink"]},
        "encoding": xy,
    })
    layers.append({
        "data": {"values": [{"x": 0.0, "y": 0.0}]},
        "mark": {"type": "text", "text": "You", "dy": 18, "fontSize": 13,
                 "fontWeight": "bold", "color": colors["ink"]},
        "encoding": xy,
    })
    return {"width": TARGET_WIDTH, "height": TARGET_HEIGHT, "layer": layers,
            "config": {"view": {"stroke": None}}}


def main() -> None:
    st.set_page_config(page_title="AlterEgo Finder", layout="wide")
    st.title("AlterEgo Finder")
    st.caption("Runs on this machine only. Your photo is never uploaded anywhere.")

    data_dir = _data_dir()
    datasets = list_datasets(data_dir)
    if not datasets:
        st.info(
            f"No indexed dataset under {data_dir}. Index one first with the CLI: "
            "python match.py --image <photo> --dataset data/<folder>"
        )
        return

    dataset = st.sidebar.selectbox(
        "Dataset", datasets, format_func=lambda p: p.name, key="dataset"
    )
    low, high = load_thresholds(dataset.parent / "config.json")
    if low is None or high is None:
        st.error(
            f"No calibrated thresholds in {dataset.parent / 'config.json'}. "
            f"Run calibrate.py first, e.g. python calibrate.py --dataset {dataset}"
        )
        return
    if low > high:
        st.error(f"config.json has threshold_low ({low}) above threshold_high ({high}).")
        return
    selected_low, selected_high = _threshold_slider(dataset, low, high)
    top = st.sidebar.slider(
        "Candidates shown", min_value=1, max_value=MAX_CANDIDATES, value=REPORT_TOP_K, key="top"
    )

    uploaded = st.file_uploader("Query photo", type=["jpg", "jpeg", "png"])
    if uploaded is None:
        st.info("Drop a photo with a face to find its closest matches.")
        return

    image_bytes = uploaded.getvalue()
    image = decode_image(image_bytes)
    if image is None:
        st.error("The image could not be read. Upload a JPEG or PNG photo.")
        return
    query = _embed_upload(image_bytes)
    if query is None:
        st.error("No face detected")
        return

    with st.spinner(f"Loading the {dataset.name} index..."):
        index = get_or_build_index(dataset)
    labeled = label_results(rank_matches(index, query.embedding), selected_low, selected_high)

    photo_col, crop_col, target_col = st.columns([1.6, 0.9, 3.5])
    photo_col.image(image, channels="BGR", caption="Your photo", width="stretch")
    crop_col.image(query.aligned_face, channels="BGR", caption="Face used for matching")
    with target_col:
        st.vega_lite_chart(
            spec=_target_spec(labeled, top, selected_low, selected_high,
                              theme=st.context.theme.type),
            width="content",
        )
        st.caption(
            "You are the cross at the centre. Distance from it = 1 - similarity "
            "(exact); direction means nothing. Hover a named face to see it."
        )

    st.subheader(f"Top {min(top, len(labeled))} of {len(labeled)} faces in {dataset.name}")
    _show_cards(labeled, top)

    report_path = data_dir / "results" / "summary.html"
    render_report(image, labeled, report_path)
    report_html = report_path.read_text(encoding="utf-8")
    st.download_button(
        "Download report (summary.html)", data=report_html,
        file_name="summary.html", mime="text/html",
    )
    with st.expander("Report preview"):
        # Our own report, with dataset folder names HTML-escaped by
        # render_report, so it is safe to embed as-is.
        st.iframe(report_html, height=600)


if __name__ == "__main__":
    main()
