#!/usr/bin/env python
"""CLI: rank a dataset's identities by similarity to a query face image, with
a HIGH_CONFIDENCE/LOW_CONFIDENCE/NO_MATCH label per candidate.

Usage:
    python match.py --image data/my_photo.jpg --dataset data/celebrities/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2

from face_pipeline.embedder import NoFaceDetectedError, extract_embedding
from face_pipeline.index import get_or_build_index, rank_matches
from face_pipeline.report import render_report

HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
NO_MATCH = "NO_MATCH"


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
        "config.json next to --dataset's parent directory).",
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

    config_low: Optional[float] = None
    config_high: Optional[float] = None
    if config_path.exists():
        try:
            payload = json.loads(config_path.read_text())
            config_low = payload.get("threshold_low")
            config_high = payload.get("threshold_high")
        except (json.JSONDecodeError, OSError):
            pass

    threshold_low = args.threshold_low if args.threshold_low is not None else config_low
    threshold_high = args.threshold_high if args.threshold_high is not None else config_high
    return threshold_low, threshold_high


def classify(score: float, threshold_low: float, threshold_high: float) -> str:
    if score >= threshold_high:
        return HIGH_CONFIDENCE
    if score >= threshold_low:
        return LOW_CONFIDENCE
    return NO_MATCH


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

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

    query_image = cv2.imread(str(image_path))
    if query_image is None:
        print(f"Error: Unable to read image file: {image_path}", file=sys.stderr)
        return 1

    try:
        query_embedding = extract_embedding(query_image)
    except NoFaceDetectedError:
        print("Error: No face detected in input image", file=sys.stderr)
        return 1

    index = get_or_build_index(dataset_path)
    results = rank_matches(index, query_embedding)

    labeled_results = [
        (entry, score, classify(score, threshold_low, threshold_high))
        for entry, score in results
    ]

    for entry, score, label in labeled_results:
        print(f"{entry.person}: {score:.4f} {label}")

    render_report(image_path, labeled_results, Path(args.report_out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
