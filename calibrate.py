#!/usr/bin/env python
"""Offline threshold calibration.

Usage:
    python calibrate.py --calibration-dir data/calibration/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from face_pipeline.calibration import (
    compute_thresholds,
    embed_calibration_dataset,
    sample_pairs,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Derive HIGH_CONFIDENCE/LOW_CONFIDENCE/NO_MATCH thresholds from a "
            "held-out calibration dataset."
        )
    )
    parser.add_argument(
        "--calibration-dir",
        default="data/calibration",
        help="Directory of LFW-style identities disjoint from the matching dataset.",
    )
    parser.add_argument(
        "--config-out",
        default=None,
        help="Where to write the computed thresholds (default: config.json next "
        "to --calibration-dir's parent, e.g. data/config.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    calibration_dir = Path(args.calibration_dir)
    config_out = (
        Path(args.config_out)
        if args.config_out
        else calibration_dir.parent / "config.json"
    )

    by_person = embed_calibration_dataset(calibration_dir)
    intra_scores, inter_scores = sample_pairs(by_person)
    threshold_low, threshold_high = compute_thresholds(intra_scores, inter_scores)

    config_out.parent.mkdir(parents=True, exist_ok=True)
    config_out.write_text(
        json.dumps(
            {"threshold_low": threshold_low, "threshold_high": threshold_high},
            indent=2,
        )
    )

    print(f"threshold_low={threshold_low:.4f} threshold_high={threshold_high:.4f}")
    print(f"Wrote {config_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
