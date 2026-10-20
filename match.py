#!/usr/bin/env python
"""CLI: rank a dataset's identities by similarity to a query face image, with
a HIGH_CONFIDENCE/LOW_CONFIDENCE/NO_MATCH label per candidate.

Usage:
    python match.py --image data/my_photo.jpg --dataset data/celebrities/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2

from face_pipeline.embedder import NoFaceDetectedError
from face_pipeline.index import get_or_build_index, rank_matches
from face_pipeline.matching import (  # noqa: F401 (re-exported for callers of match.py)
    HIGH_CONFIDENCE,
    LOW_CONFIDENCE,
    NO_MATCH,
    classify,
    embed_query,
    label_results,
    load_thresholds,
)
from face_pipeline.report import REPORT_TOP_K, render_report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Match a query face image against a dataset of labeled face images."
    )
    parser.add_argument("--image", required=True, help="Path to the query face image.")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to a dataset directory (one subfolder per person, LFW-style).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the calibrated-thresholds config.json (default: "
        "config.json in --dataset's parent directory, e.g. data/config.json).",
    )
    parser.add_argument(
        "--threshold-low",
        type=float,
        default=None,
        help="Override the NO_MATCH / LOW_CONFIDENCE boundary from config.json.",
    )
    parser.add_argument(
        "--threshold-high",
        type=float,
        default=None,
        help="Override the LOW_CONFIDENCE / HIGH_CONFIDENCE boundary from config.json.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=REPORT_TOP_K,
        help=f"How many top-ranked candidates to print (default: {REPORT_TOP_K}).",
    )
    parser.add_argument(
        "--report-out",
        default="data/results/summary.html",
        help="Where to write the self-contained HTML match report "
        "(default: data/results/summary.html). Not written if the query "
        "image has no detectable face.",
    )
    return parser


def _load_thresholds(
    args: argparse.Namespace, dataset_path: Path
) -> Tuple[Optional[float], Optional[float]]:
    config_path = Path(args.config) if args.config else dataset_path.parent / "config.json"
    config_low, config_high = load_thresholds(config_path)

    threshold_low = args.threshold_low if args.threshold_low is not None else config_low
    threshold_high = args.threshold_high if args.threshold_high is not None else config_high
    return threshold_low, threshold_high


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error("--top must be at least 1")

    image_path = Path(args.image)
    dataset_path = Path(args.dataset)

    threshold_low, threshold_high = _load_thresholds(args, dataset_path)
    if threshold_low is None or threshold_high is None:
        print(
            "Error: No calibrated thresholds available. Run calibrate.py "
            "first, or pass --threshold-low/--threshold-high.",
            file=sys.stderr,
        )
        return 1
    if threshold_low > threshold_high:
        print(
            f"Error: threshold_low ({threshold_low}) is above threshold_high "
            f"({threshold_high}), so nothing could be LOW_CONFIDENCE.",
            file=sys.stderr,
        )
        return 1

    if not dataset_path.is_dir():
        print(f"Error: Dataset directory not found: {dataset_path}", file=sys.stderr)
        return 1

    query_image = cv2.imread(str(image_path))
    if query_image is None:
        print(f"Error: Unable to read image file: {image_path}", file=sys.stderr)
        return 1

    # Embed before indexing, so an image with no face fails fast instead of
    # first building (and caching) the dataset's index.
    try:
        query = embed_query(query_image)
    except NoFaceDetectedError:
        print("Error: No face detected in input image", file=sys.stderr)
        return 1

    index = get_or_build_index(dataset_path)
    labeled_results = label_results(
        rank_matches(index, query.embedding), threshold_low, threshold_high
    )

    for entry, score, label in labeled_results[: args.top]:
        print(f"{entry.person}: {score:.4f} {label}")

    render_report(image_path, labeled_results, Path(args.report_out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
