"""Web UI: drop a face photo, pick an indexed dataset, and see the top
candidates with similarity scores and calibrated confidence labels.

Run from the repository root (so .streamlit/config.toml applies and the page
is served on localhost only):

    pip install -r requirements-ui.txt
    streamlit run app.py
"""

from __future__ import annotations

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
    QueryFace,
    embed_query,
    label_results,
    load_thresholds,
)
from face_pipeline.report import REPORT_TOP_K, render_report

MAX_CANDIDATES = 20
CARDS_PER_ROW = 5
_LABEL_COLORS = {HIGH_CONFIDENCE: "green", LOW_CONFIDENCE: "orange"}  # NO_MATCH: gray


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
        help="Below low: NO_MATCH. From low: LOW_CONFIDENCE. From high: HIGH_CONFIDENCE.",
    )
    if (round(selected[0], 4), round(selected[1], 4)) != (round(low, 4), round(high, 4)):
        st.sidebar.warning(
            f"Thresholds overridden: the calibrated values are low {low:.4f}, high {high:.4f}."
        )
    return selected


def _show_cards(labeled, top: int) -> None:
    shown = labeled[:top]
    for row_start in range(0, len(shown), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW)
        for offset, (entry, score, label) in enumerate(shown[row_start: row_start + CARDS_PER_ROW]):
            with columns[offset]:
                image = cv2.imread(str(entry.filepath))
                if image is not None:
                    st.image(image, channels="BGR", width="stretch")
                # Person names are dataset folder names, i.e. untrusted input:
                # st.text shows them literally, with no Markdown or HTML.
                st.text(f"#{row_start + offset + 1} {entry.person}")
                color = _LABEL_COLORS.get(label, "gray")
                st.markdown(f"`{score:.4f}` :{color}[**{label}**]")


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

    photo_col, crop_col, _ = st.columns([2, 1, 3])
    photo_col.image(image, channels="BGR", caption="Your photo", width="stretch")
    crop_col.image(query.aligned_face, channels="BGR", caption="Face used for matching")

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
