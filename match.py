#!/usr/bin/env python
"""CLI: rank a dataset's identities by similarity to a query face image.

Usage:
    python match.py --image data/my_photo.jpg --dataset data/celebrities/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

from face_pipeline.embedder import NoFaceDetectedError, extract_embedding
from face_pipeline.index import get_or_build_index, rank_matches


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    image_path = Path(args.image)
    dataset_path = Path(args.dataset)

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

    for entry, score in results:
        print(f"{entry.person}: {score:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
