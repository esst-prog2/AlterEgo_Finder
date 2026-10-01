#!/usr/bin/env python
"""HW4 spike (issue #4): at what index size does a stranger's top match
cross threshold_high?

Calibrates thresholds on 200 held-out LFW identities (same code path as
calibrate.py), builds nested one-image-per-identity indexes of 50, 500 and
5000 faces, then queries 200 identities that are in none of them and counts
how many top-1 scores land at or above each threshold (match.py's >=).

Throwaway spike code. Writes data/spike_results.json.

Usage:
    python spike_eval.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import tarfile
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from face_pipeline.calibration import compute_thresholds, sample_pairs
from face_pipeline.embedder import NoFaceDetectedError, extract_embedding

# Original LFW, via the figshare mirror scikit-learn uses; SHA-256 is the one
# published in sklearn/datasets/_lfw.py. (The deep-funneled tarball's UMass
# host no longer resolves -- see PLANNING_LOG.md, 2026-10-01.)
LFW_URL = "https://ndownloader.figshare.com/files/5976018"
LFW_SHA256 = "055f7d9c632d7370e6fb4afc7468d40f970c34a80d4c6f50ffec63f5a8d536c0"

ROOT = Path(__file__).resolve().parent
LFW_DIR = ROOT / "data" / "lfw"  # gitignored
TARBALL = LFW_DIR / "lfw.tgz"
IMAGES_DIR = LFW_DIR / "lfw"
EMBED_CACHE = LFW_DIR / "spike_embeddings.npz"
RESULTS_PATH = ROOT / "data" / "spike_results.json"

SEED = 0
N_CALIBRATION = 200
N_QUERIES = 200
INDEX_SIZES = (50, 500, 5000)
MAX_CALIBRATION_IMAGES = 4


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_lfw() -> None:
    if not TARBALL.exists():
        LFW_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {LFW_URL} ...")
        urllib.request.urlretrieve(LFW_URL, TARBALL)
    digest = sha256(TARBALL)
    if digest != LFW_SHA256:
        sys.exit(f"LFW checksum mismatch: got {digest}, expected {LFW_SHA256}")
    if not IMAGES_DIR.exists():
        print("Extracting ...")
        with tarfile.open(TARBALL) as tar:
            tar.extractall(LFW_DIR)


def load_cache() -> dict:
    if EMBED_CACHE.exists():
        with np.load(EMBED_CACHE) as data:
            return {k: data[k] for k in data.files}
    return {}


def embed(rel: str, cache: dict) -> np.ndarray | None:
    """L2-normalized embedding of an LFW image, or None if no face is found.
    Failures are cached as a zero vector."""
    if rel not in cache:
        image = cv2.imread(str(IMAGES_DIR / rel))
        try:
            vec = extract_embedding(image)
            vec = vec / np.linalg.norm(vec)
        except NoFaceDetectedError:
            vec = np.zeros(512, dtype=np.float32)
        cache[rel] = vec.astype(np.float32)
        if len(cache) % 250 == 0:
            print(f"  embedded {len(cache)} images")
            np.savez(EMBED_CACHE, **cache)
    vec = cache[rel]
    return None if not vec.any() else vec


def main() -> int:
    fetch_lfw()
    people = {
        p.name: sorted(f"{p.name}/{img.name}" for img in p.glob("*.jpg"))
        for p in sorted(IMAGES_DIR.iterdir())
        if p.is_dir()
    }
    rng = random.Random(SEED)
    multi = sorted(n for n, imgs in people.items() if len(imgs) >= 2)
    calibration_ids = rng.sample(multi, N_CALIBRATION)
    rest = sorted(set(people) - set(calibration_ids))
    rng.shuffle(rest)
    print(f"{len(people)} identities; {len(rest)} left for queries + index")

    cache = load_cache()

    # Calibration: same pair sampling + threshold search as calibrate.py.
    by_person = {}
    for name in calibration_ids:
        vecs = [embed(r, cache) for r in people[name][:MAX_CALIBRATION_IMAGES]]
        vecs = [v for v in vecs if v is not None]
        if vecs:
            by_person[name] = vecs
    intra, inter = sample_pairs(by_person)
    threshold_low, threshold_high = compute_thresholds(intra, inter)
    print(f"threshold_low={threshold_low:.4f} threshold_high={threshold_high:.4f}")

    # Queries first, then the index, each skipping identities with no detected
    # face, so the two sets stay disjoint and hit their target sizes.
    queries, index = [], []
    for name in rest:
        target = queries if len(queries) < N_QUERIES else index
        if len(index) == max(INDEX_SIZES):
            break
        vec = embed(people[name][0], cache)
        if vec is not None:
            target.append((name, vec))
    np.savez(EMBED_CACHE, **cache)
    if len(index) < max(INDEX_SIZES):
        sys.exit(f"Only {len(index)} index faces available")

    query_matrix = np.stack([v for _, v in queries])
    index_matrix = np.stack([v for _, v in index])

    per_size = []
    for n in INDEX_SIZES:
        scores = query_matrix @ index_matrix[:n].T  # (queries, n) cosine
        top1 = scores.max(axis=1)
        above_high = int((top1 >= threshold_high).sum())
        above_low = int((top1 >= threshold_low).sum())
        per_size.append(
            {
                "index_size": n,
                "queries": len(queries),
                "top1_at_or_above_threshold_high": above_high,
                "top1_at_or_above_threshold_low": above_low,
                "far_high": above_high / len(queries),
                "far_low": above_low / len(queries),
                "top1_score_mean": float(top1.mean()),
                "top1_score_p99": float(np.percentile(top1, 99)),
                "top1_score_max": float(top1.max()),
            }
        )
        print(
            f"N={n:>5}: >=high {above_high}/{len(queries)} "
            f"({above_high / len(queries):.1%}), >=low {above_low}/{len(queries)} "
            f"({above_low / len(queries):.1%}), top-1 max {top1.max():.4f}"
        )

    results = {
        "lfw_url": LFW_URL,
        "lfw_sha256": LFW_SHA256,
        "seed": SEED,
        "calibration": {
            "identities": len(by_person),
            "genuine_pairs": len(intra),
            "impostor_pairs": len(inter),
            "threshold_low": threshold_low,
            "threshold_high": threshold_high,
            "pairwise_far_at_high": float(np.mean(np.array(inter) >= threshold_high)),
        },
        "results": per_size,
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
