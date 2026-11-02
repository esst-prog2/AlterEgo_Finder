#!/usr/bin/env python
"""Take a fresh clone to a working program: download LFW, build the candidate
and calibration datasets from the committed list data/lfw_split.json, calibrate
the thresholds and index the candidates. Safe to run again.

The list holds file paths only; the images are downloaded here and never
committed. Everyone gets the same faces, so README section 1's scores reproduce.

Usage (from the repository root):
    python setup_data.py
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import sys
import tarfile
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

import calibrate
from face_pipeline.index import get_or_build_index
from face_pipeline.weights import ModelWeightError

# Original LFW, via the figshare mirror scikit-learn uses; the SHA-256 is the
# one published in sklearn/datasets/_lfw.py (see spike_eval.py).
LFW_URL = "https://ndownloader.figshare.com/files/5976018"
LFW_SHA256 = "055f7d9c632d7370e6fb4afc7468d40f970c34a80d4c6f50ffec63f5a8d536c0"

ROOT = Path(__file__).resolve().parent
ARCHIVE_PREFIX = "lfw/"  # where the images sit inside the archive
DOWNLOAD_TIMEOUT_S = 60  # per network read, so a stalled download fails instead of hanging
CHUNK_SIZE = 1 << 20  # 1 MiB


class SetupError(Exception):
    """A failure to report to the user as one clear message."""


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download LFW, build data/celebrities and data/calibration, "
        "and calibrate the thresholds. Safe to run again."
    )
    parser.add_argument(
        "--data-dir", default=str(ROOT / "data"), help="Where to build the datasets."
    )
    parser.add_argument(
        "--tarball",
        default=None,
        help="Use this copy of lfw.tgz instead of downloading it (checksum still verified).",
    )
    parser.add_argument(
        "--recalibrate",
        action="store_true",
        help="Compute the thresholds again even if config.json already exists.",
    )
    parser.add_argument(
        "--split",
        default=str(ROOT / "data" / "lfw_split.json"),
        help="The list of images to use for each dataset.",
    )
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(destination: Path) -> None:
    """Download and verify the archive; it gets its final name only once verified."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + ".part")
    print(f"Downloading LFW (about 180 MB) from {LFW_URL} ...")
    try:
        with urllib.request.urlopen(LFW_URL, timeout=DOWNLOAD_TIMEOUT_S) as response:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            next_report = 10
            with part.open("wb") as out:
                for chunk in iter(lambda: response.read(CHUNK_SIZE), b""):
                    out.write(chunk)
                    done += len(chunk)
                    if total and done * 100 // total >= next_report:
                        print(f"  {next_report}%")
                        next_report += 10
        if _sha256(part) != LFW_SHA256:
            raise SetupError(
                "The downloaded archive failed its checksum check, so it was not used. "
                "Run setup_data.py again to retry."
            )
        os.replace(part, destination)
    except (OSError, http.client.HTTPException) as e:
        raise SetupError(
            f"Could not download LFW ({e}). Run setup_data.py again to retry, or pass "
            "a copy you already have with --tarball."
        ) from e
    finally:
        part.unlink(missing_ok=True)


def _archive(tarball: Optional[str], data_dir: Path) -> Path:
    if tarball:
        path = Path(tarball)
        if not path.is_file():
            raise SetupError(f"Archive not found: {path}")
        if _sha256(path) != LFW_SHA256:
            raise SetupError(f"{path} failed its checksum check, so it was not used.")
        return path
    path = data_dir / "lfw" / "lfw.tgz"
    if not (path.is_file() and _sha256(path) == LFW_SHA256):
        _download(path)
    return path


def _extract(archive: Path, wanted: Dict[str, Path]) -> None:
    """Write the wanted images (archive-relative path -> destination).

    One sequential pass over the archive: looking members up by name in a .tgz
    takes minutes. Output paths come from the committed list, never from the
    archive, and each file appears under its final name only once complete.
    """
    remaining = dict(wanted)
    try:
        with tarfile.open(archive, "r|gz") as tar:
            for member in tar:
                if not remaining:
                    break
                relative = member.name[len(ARCHIVE_PREFIX):]
                if not (member.isfile() and member.name.startswith(ARCHIVE_PREFIX)
                        and relative in remaining):
                    continue
                destination = remaining.pop(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                part = destination.with_name(destination.name + ".part")
                part.write_bytes(tar.extractfile(member).read())
                os.replace(part, destination)
    except (tarfile.TarError, OSError, EOFError) as e:
        raise SetupError(f"Could not read {archive}: {e}") from e
    if remaining:
        listed = ", ".join(sorted(remaining)[:5])
        raise SetupError(f"{len(remaining)} listed images are not in the archive: {listed}")


def _missing_images(split: Dict[str, List[str]], data_dir: Path) -> Dict[str, Path]:
    missing = {}
    for dataset, relatives in split.items():
        for relative in relatives:
            if ".." in relative or relative.startswith(("/", "\\")):
                raise SetupError(f"Unsafe path in the dataset list: {relative}")
            destination = data_dir / dataset / relative
            if not destination.exists():
                missing[relative] = destination
    return missing


def run(args: argparse.Namespace) -> None:
    data_dir = Path(args.data_dir)
    try:
        split = json.loads(Path(args.split).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SetupError(f"Could not read the dataset list {args.split}: {e}") from e

    missing = _missing_images(split, data_dir)
    if missing:
        archive = _archive(args.tarball, data_dir)
        print(f"Building {len(missing)} images in {data_dir} ...")
        _extract(archive, missing)
    else:
        print("Datasets already built.")

    celebrities, calibration = data_dir / "celebrities", data_dir / "calibration"
    config = data_dir / "config.json"
    try:
        if args.recalibrate or not config.exists():
            print("Calibrating the thresholds (a few minutes) ...")
            status = calibrate.main([
                "--calibration-dir", str(calibration),
                "--dataset", str(celebrities),
                "--config-out", str(config),
            ])
            if status != 0:
                raise SetupError("Calibration failed; see the message above.")
        else:
            print(f"Keeping the thresholds in {config} (--recalibrate to redo them).")
            get_or_build_index(celebrities)
    except ModelWeightError as e:
        raise SetupError(f"Could not get the model weights ({e}). Run setup_data.py again.") from e


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        run(args)
    except SetupError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print("Done. Start the web UI with: streamlit run app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
