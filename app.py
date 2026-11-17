"""Web UI: drop a face photo, pick an indexed dataset, and see the top
candidates with similarity scores and calibrated confidence labels.

Run from the repository root (so .streamlit/config.toml applies and the page
is served on localhost only):

    pip install -r requirements-ui.txt
    streamlit run app.py
"""

from __future__ import annotations

import base64
import html
import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import streamlit as st

from face_pipeline.attribution import credit_for, load_attribution, safe_source_url
from face_pipeline.embedder import NoFaceDetectedError
from face_pipeline.images import read_image
from face_pipeline.index import CACHE_DIRNAME, EMBEDDINGS_FILENAME, get_or_build_index, rank_matches
from face_pipeline.matching import (
    HIGH_CONFIDENCE,
    LOW_CONFIDENCE,
    NO_MATCH,
    QueryFace,
    config_path_for,
    embed_query,
    label_results,
    load_thresholds,
)
from face_pipeline.report import REPORT_TOP_K, render_report
from face_pipeline.target import (
    CHAR_PX,
    LINE_PX,
    NAME_PLACES,
    place_names,
    ring,
    target_points,
)

MAX_CANDIDATES = 20
# The shared logo (DESIGN.md): the target in miniature, and the lockup with the name.
STATIC_DIR = Path(__file__).resolve().parent / "static"
LOGO_MARK = STATIC_DIR / "logo-mark.svg"
LOGO_LOCKUP = STATIC_DIR / "logo-lockup.png"
CARDS_PER_ROW = 5
CARD_AUTHOR_CHARS = 60
_LABEL_COLORS = {HIGH_CONFIDENCE: "green", LOW_CONFIDENCE: "orange"}  # NO_MATCH: gray
# The page shows only these plain names. The technical labels are for the
# developers: they stay in the CLI, the HTML report and the specs.
PLAIN_NAMES = {HIGH_CONFIDENCE: "Same person", LOW_CONFIDENCE: "Alter Ego", NO_MATCH: "Not You"}
THUMBNAIL_PX = 128  # longest side of the tooltip face thumbnails (top N only)
CARD_PHOTO_PX = 320  # side of the square card photos
# Readable dataset names; the folder name stays visible because README section 1
# names folders. Any other folder is shown as it is.
DATASET_LABELS = {"wikidata": "Public figures", "celebrities": "LFW faces"}
DEFAULT_DATASET = "wikidata"
_LABEL_HEX = {HIGH_CONFIDENCE: "#1a7f37", LOW_CONFIDENCE: "#d4a72c", NO_MATCH: "#8c959f"}
# DESIGN.md beyond what Streamlit's theme can set: the paper's grid, navy frames,
# capitals in the display face, ink score figures, readable captions, a target
# that shrinks with its column. Selectors are Streamlit's test ids and our own
# classes only (tests/test_app.py checks the list); keyed containers carry the
# class st-key-<key>.
STYLESHEET = """<style>
[data-testid="stApp"] {
  background-image: linear-gradient(rgba(29, 60, 120, 0.09) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(29, 60, 120, 0.09) 1px, transparent 1px);
  background-size: 24px 24px;
}
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2 { text-transform: uppercase; letter-spacing: 0.005em; }
[data-testid="stCaptionContainer"] { color: #46505d; opacity: 1; }
[data-testid="stFileUploaderDropzone"] { border: 2px solid #1d3c78; border-radius: 0; }
[data-testid="stAlertContentInfo"], [data-testid="stAlertContainer"] { color: #1d3c78; }
[class*="st-key-ae-card-"] {
  border: 2px solid #1d3c78 !important; border-radius: 0 !important; background: #f8fbfd;
  box-shadow: 0 1px 0 #1d3c78, 0 10px 28px -18px rgba(29, 60, 120, 0.45);
}
[class*="st-key-ae-name-"] [data-testid="stText"] {
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif; font-weight: 700;
  font-size: 1.05rem; text-transform: uppercase; letter-spacing: 0.02em; color: #1f2328;
}
[class*="st-key-ae-card-"] code {
  font-family: "Barlow Condensed", "Arial Narrow", sans-serif; font-weight: 700; font-size: 1.35rem;
  color: #1f2328; background: transparent; padding: 0; font-variant-numeric: tabular-nums;
}
[data-testid="stVegaLiteChart"] canvas, [data-testid="stVegaLiteChart"] svg { max-width: 100%; height: auto; }
.ae-photo { display: block; width: 100%; aspect-ratio: 1 / 1; object-fit: cover; }
.ae-verdict { margin: 0.2rem 0 0; padding: 0.7rem 0.9rem; border: 2px solid #1d3c78; background: #f8fbfd;
  font-size: 1.15rem; line-height: 1.5; color: #1f2328; }
.ae-verdict .ae-name, .ae-verdict .ae-score { font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700; font-size: 1.45rem; text-transform: uppercase; font-variant-numeric: tabular-nums; }
.ae-chip { display: inline-flex; align-items: center; gap: 0.4em; font-family: "Barlow Condensed", "Arial Narrow", sans-serif;
  font-weight: 700; font-size: 1.05rem; text-transform: uppercase; letter-spacing: 0.03em; white-space: nowrap; }
.ae-dot { display: inline-block; width: 0.8em; height: 0.8em; border-radius: 50%; border: 1.5px solid #1f2328; }
</style>"""
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
    "light": {"ink": "#1f2328", "muted": "#46505d", "faint": "#8c959f"},
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


def _dataset_label(path: Path) -> str:
    """A readable name that keeps the folder name visible, e.g. "Public figures (wikidata)"."""
    readable = DATASET_LABELS.get(path.name)
    return f"{readable} ({path.name})" if readable else path.name


def _default_dataset_index(datasets: List[Path]) -> int:
    names = [p.name for p in datasets]
    return names.index(DEFAULT_DATASET) if DEFAULT_DATASET in names else 0


def _verdict(labeled):
    """(kind, person, score) of the answer in one line.

    kind is "same" (the top face is Same person), "alter" (nobody is the same
    person; the closest Alter Ego) or "none" (nobody is close).
    """
    entry, score, label = labeled[0]
    if label == HIGH_CONFIDENCE:
        return "same", entry.person, score
    if label == LOW_CONFIDENCE:
        return "alter", entry.person, score
    return "none", entry.person, score


def _chip(label: str) -> str:
    return (f'<span class="ae-chip"><i class="ae-dot" style="background: {_LABEL_HEX[label]}"></i>'
            f'{PLAIN_NAMES[label]}</span>')


def _verdict_html(labeled) -> str:
    """The verdict line. Person names are dataset folder names, i.e. untrusted: escaped."""
    kind, person, score = _verdict(labeled)
    name = f'<span class="ae-name">{html.escape(person)}</span>'
    figure = f'<span class="ae-score">{score:.4f}</span>'
    if kind == "same":
        text = f"Closest: {name} &middot; {figure} &middot; {_chip(HIGH_CONFIDENCE)}"
    elif kind == "alter":
        text = (f"Nobody here is the same person. Closest Alter Ego: {name} &middot; {figure} "
                f"&middot; {_chip(LOW_CONFIDENCE)}")
    else:
        text = (f"Nobody in this dataset is close. {_chip(NO_MATCH)} "
                f"(the closest, {name}, scores {figure})")
    return f'<p class="ae-verdict">{text}</p>'


def _zones_line(low: float, high: float) -> str:
    return (f"{PLAIN_NAMES[HIGH_CONFIDENCE]}: {high:.4f} or more. "
            f"{PLAIN_NAMES[LOW_CONFIDENCE]}: from {low:.4f}, one of the closest public figures, but not you. "
            f"{PLAIN_NAMES[NO_MATCH]}: below {low:.4f}.")


def _square_crop(image: np.ndarray) -> np.ndarray:
    """The centred square of ``image``, so every card picture has the same shape."""
    height, width = image.shape[:2]
    side = min(height, width)
    top, left = (height - side) // 2, (width - side) // 2
    return image[top: top + side, left: left + side]


def _short_author(credit: dict) -> str:
    """The author for a narrow card; the source page and the report have it in full."""
    author = credit.get("author", "")
    return author if len(author) <= CARD_AUTHOR_CHARS else author[:CARD_AUTHOR_CHARS - 3].rstrip() + "..."


@st.cache_data(show_spinner=False, max_entries=1024)
def _card_photo(path: str) -> str:
    """The square card photo of the image at ``path`` as a JPEG data URI, or "" if unreadable."""
    image = read_image(path)
    if image is None:
        return ""
    square = cv2.resize(_square_crop(image), (CARD_PHOTO_PX, CARD_PHOTO_PX), interpolation=cv2.INTER_AREA)
    ok, buffer = cv2.imencode(".jpg", square, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("ascii") if ok else ""


def _show_cards(labeled, top: int, credits: Optional[dict] = None) -> None:
    shown = labeled[:top]
    for row_start in range(0, len(shown), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW)
        for offset, (entry, score, label) in enumerate(shown[row_start: row_start + CARDS_PER_ROW]):
            rank = row_start + offset + 1
            # A keyed container carries the class st-key-<key>, which the
            # stylesheet frames in navy.
            with columns[offset], st.container(border=True, key=f"ae-card-{rank}"):
                photo = _card_photo(str(entry.filepath))
                if photo:
                    # st.image has no alt text; the name is escaped (untrusted).
                    st.html(f'<img class="ae-photo" src="{photo}" '
                            f'alt="Photo of {html.escape(entry.person, quote=True)}">')
                # Person names are dataset folder names, i.e. untrusted input:
                # st.text shows them literally, with no Markdown or HTML.
                with st.container(key=f"ae-name-{rank}"):
                    st.text(f"#{rank} {entry.person}")
                color = _LABEL_COLORS.get(label, "gray")
                # The label word stays ink on a wash of its label colour: gold
                # text on the paper would be too faint to read.
                st.markdown(f"`{score:.4f}` :{color}-background[**{PLAIN_NAMES[label]}**]")
                credit = credit_for(credits, entry.filepath)
                if credit:
                    # Credits are text from strangers: st.text shows them literally,
                    # and only Commons pages become links.
                    st.text(f"Photo: {_short_author(credit)}, {credit.get('license', '')}")
                    source = safe_source_url(credit.get("source", ""))
                    if source:
                        st.markdown(f"[Source]({source})")


@st.cache_data(show_spinner=False, max_entries=1024)
def _thumbnail(path: str) -> str:
    """A small JPEG data URI of the image at ``path``, or "" if unreadable."""
    image = read_image(path)
    if image is None:
        return ""
    height, width = image.shape[:2]
    scale = THUMBNAIL_PX / max(height, width)
    small = cv2.resize(image, (max(1, round(width * scale)), max(1, round(height * scale))),
                       interpolation=cv2.INTER_AREA)
    ok, buffer = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("ascii") if ok else ""


def _target_spec(labeled, top: int, low: float, high: float, theme: Optional[str] = None,
                 credits: Optional[dict] = None) -> dict:
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
    if credits:
        named_tooltip.append({"field": "photo", "type": "nominal", "title": "Photo"})
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
            credit = credit_for(credits, p.filepath) if named else None
            if credit:
                row["photo"] = f"{_short_author(credit)}, {credit.get('license', '')}"
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
    # Each ring in the colour of the zone it closes: gold for Alter Ego (low),
    # green for Same person (high), as on the promo page and in the video.
    ring_colors = dict(zip(_TARGET_COLORS["domain"], _TARGET_COLORS["range"]))
    for threshold, zone in ((low, PLAIN_NAMES[LOW_CONFIDENCE]), (high, PLAIN_NAMES[HIGH_CONFIDENCE])):
        xs, ys = ring(threshold)
        layers.append({
            "data": {"values": [{"x": x, "y": y, "i": i} for i, (x, y) in enumerate(zip(xs, ys))]},
            "mark": {"type": "line", "strokeWidth": 2, "color": ring_colors[zone]},
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
    # other, and move to another side only if that place is taken. They go
    # through Vega's SVG text, which does not interpret HTML.
    def chart_x(x):
        return TARGET_WIDTH / 2 * (1 + x / half_x)

    def chart_y(y):
        return TARGET_HEIGHT / 2 * (1 - y / half_y)

    legend_left = chart_x(-0.97 * half_x)
    legend_box = (legend_left, chart_y(0.95 * half_y) - LINE_PX / 2,
                  legend_left + max(map(len, legend)) * CHAR_PX, chart_y(0.8 * half_y) + LINE_PX / 2)
    named = sorted((p for p in points if p.named), key=lambda p: p.rank)
    name_texts = [f"#{p.rank} {p.person}" + (f" ({p.score:.4f})" if p.rank == 1 else "") for p in named]
    places = place_names([(chart_x(p.x), chart_y(p.y), text) for p, text in zip(named, name_texts)],
                         TARGET_WIDTH, TARGET_HEIGHT, legend_box)
    for place, (align, dx, dy) in NAME_PLACES.items():
        rows = [{"x": p.x, "y": p.y, "text": text}
                for p, text, chosen in zip(named, name_texts, places) if chosen == place]
        if rows:
            layers.append({
                "data": {"values": rows},
                "mark": {"type": "text", "align": align, "dx": dx, "dy": dy, "baseline": "middle",
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
    shown = [p for p in points if p.named]
    counts = {label: sum(p.label == label for p in shown) for label in PLAIN_NAMES}
    description = (f"Similarity target: {len(shown)} faces shown; "
                   f"{counts[HIGH_CONFIDENCE]} inside the {PLAIN_NAMES[HIGH_CONFIDENCE]} ring, "
                   f"{counts[LOW_CONFIDENCE]} between the rings ({PLAIN_NAMES[LOW_CONFIDENCE]}), "
                   f"{counts[NO_MATCH]} outside ({PLAIN_NAMES[NO_MATCH]}).")
    return {"width": TARGET_WIDTH, "height": TARGET_HEIGHT, "layer": layers, "description": description,
            "config": {"view": {"stroke": None}}}


def main() -> None:
    st.set_page_config(page_title="AlterEgo Finder", layout="wide", page_icon=str(LOGO_MARK))
    st.logo(str(LOGO_LOCKUP), size="large", icon_image=str(LOGO_MARK))
    st.html(STYLESHEET)
    st.title("AlterEgo Finder")
    st.caption("Runs on this machine only. Your photo is never uploaded anywhere.")

    data_dir = _data_dir()
    datasets = list_datasets(data_dir)
    if not datasets:
        st.info(
            f"No indexed dataset under {data_dir}. To set up the standard one, run "
            "`python setup_data.py`, then refresh this page. To use your own, index it once with "
            "`python match.py --image <photo> --dataset data/<folder>`."
        )
        return

    dataset = st.sidebar.selectbox(
        "Dataset", datasets, index=_default_dataset_index(datasets), format_func=_dataset_label,
        key="dataset",
    )
    config_path = config_path_for(dataset)
    low, high = load_thresholds(config_path)
    if low is None or high is None:
        st.error(
            f"No calibrated thresholds in {config_path}. "
            f"Run calibrate.py first, e.g. python calibrate.py --dataset {dataset}"
        )
        return
    if low > high:
        st.error(f"config.json has threshold_low ({low}) above threshold_high ({high}).")
        return
    # The page always uses the calibrated thresholds; overrides stay in the CLI
    # (match.py --threshold-low/--threshold-high).
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
        st.error(
            "No face detected. It is usually found when one face looks roughly at the camera and "
            "fills a good part of the photo: try a sharper, front-facing photo, or crop it closer "
            "to the face."
        )
        return

    with st.spinner(f"Loading the {dataset.name} index..."):
        index = get_or_build_index(dataset)
    labeled = label_results(rank_matches(index, query.embedding), low, high)
    credits = load_attribution(dataset)

    # The answer first, in one sentence, then the evidence.
    st.html(_verdict_html(labeled))
    st.caption(_zones_line(low, high))

    photo_col, target_col = st.columns([1, 3.4])
    with photo_col:
        st.image(image, channels="BGR", caption="Your photo", width=160)
        st.image(query.aligned_face, channels="BGR", caption="Face used for matching", width=112)
    with target_col:
        st.vega_lite_chart(
            spec=_target_spec(labeled, top, low, high, theme=st.context.theme.type, credits=credits),
            width="content",
        )
        st.caption(
            "You are the cross at the centre. Distance from it = 1 - similarity "
            "(exact); direction means nothing. Hover a named face to see it."
        )

    st.header(f"Top {min(top, len(labeled))} of {len(labeled)} faces in {_dataset_label(dataset)}")
    _show_cards(labeled, top, credits)

    report_path = data_dir / "results" / "summary.html"
    render_report(image, labeled, report_path, attribution=credits)
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
