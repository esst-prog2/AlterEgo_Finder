"""Dataset indexing: embed all images under a dataset directory into a cached,
L2-normalized embedding matrix, with a sidecar manifest for staleness checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

import cv2
import numpy as np

from face_pipeline.embedder import EMBEDDING_SIZE, NoFaceDetectedError, extract_embedding

CACHE_DIRNAME = ".matchcache"
EMBEDDINGS_FILENAME = "embeddings.npy"
MANIFEST_FILENAME = "manifest.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass
class IndexEntry:
    person: str
    filepath: Path


@dataclass
class DatasetIndex:
    embeddings: np.ndarray  # (N, EMBEDDING_SIZE), L2-normalized rows
    entries: List[IndexEntry]


def _iter_dataset_images(dataset_dir: Path) -> Iterator[Tuple[str, Path]]:
    for person_dir in sorted(p for p in dataset_dir.iterdir() if p.is_dir()):
        for image_path in sorted(person_dir.iterdir()):
            if image_path.suffix.lower() in IMAGE_EXTENSIONS:
                yield person_dir.name, image_path


def _cache_paths(dataset_dir: Path) -> Tuple[Path, Path]:
    cache_dir = dataset_dir / CACHE_DIRNAME
    return cache_dir / EMBEDDINGS_FILENAME, cache_dir / MANIFEST_FILENAME


def _current_file_manifest(dataset_dir: Path) -> Dict[str, dict]:
    manifest = {}
    for person, image_path in _iter_dataset_images(dataset_dir):
        rel = str(image_path.relative_to(dataset_dir))
        stat = image_path.stat()
        manifest[rel] = {"size": stat.st_size, "mtime": stat.st_mtime, "person": person}
    return manifest


def _is_cache_fresh(dataset_dir: Path, manifest_path: Path) -> bool:
    if not manifest_path.exists():
        return False
    try:
        payload = json.loads(manifest_path.read_text())
        cached_files = payload["files"]
    except (json.JSONDecodeError, OSError, KeyError):
        return False
    return cached_files == _current_file_manifest(dataset_dir)


def build_index(dataset_dir: Path) -> DatasetIndex:
    """Extract L2-normalized embeddings for every image under ``dataset_dir``.

    Images with no detectable face, or that fail to load, are skipped.
    """
    embeddings: List[np.ndarray] = []
    entries: List[IndexEntry] = []

    for person, image_path in _iter_dataset_images(dataset_dir):
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        try:
            embedding = extract_embedding(image)
        except NoFaceDetectedError:
            continue

        norm = np.linalg.norm(embedding)
        if norm == 0:
            continue
        embeddings.append((embedding / norm).astype(np.float32))
        entries.append(IndexEntry(person=person, filepath=image_path))

    matrix = (
        np.stack(embeddings)
        if embeddings
        else np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
    )
    return DatasetIndex(embeddings=matrix, entries=entries)


def _save_cache(dataset_dir: Path, index: DatasetIndex) -> None:
    embeddings_path, manifest_path = _cache_paths(dataset_dir)
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_path, index.embeddings)

    entries_payload = [
        {"person": e.person, "filepath": str(e.filepath.relative_to(dataset_dir))}
        for e in index.entries
    ]
    payload = {"files": _current_file_manifest(dataset_dir), "entries": entries_payload}
    manifest_path.write_text(json.dumps(payload, indent=2))


def _load_cache(dataset_dir: Path) -> DatasetIndex:
    embeddings_path, manifest_path = _cache_paths(dataset_dir)
    embeddings = np.load(embeddings_path)
    payload = json.loads(manifest_path.read_text())
    entries = [
        IndexEntry(person=e["person"], filepath=dataset_dir / e["filepath"])
        for e in payload["entries"]
    ]
    return DatasetIndex(embeddings=embeddings, entries=entries)


def get_or_build_index(dataset_dir: Path) -> DatasetIndex:
    """Return a cached index if fresh, otherwise build, cache, and return a new one."""
    embeddings_path, manifest_path = _cache_paths(dataset_dir)
    if embeddings_path.exists() and _is_cache_fresh(dataset_dir, manifest_path):
        return _load_cache(dataset_dir)

    index = build_index(dataset_dir)
    _save_cache(dataset_dir, index)
    return index


def rank_matches(
    index: DatasetIndex, query_embedding: np.ndarray
) -> List[Tuple[IndexEntry, float]]:
    """Rank indexed entries by cosine similarity to ``query_embedding``, most similar first.

    Assumes ``index.embeddings`` rows are already L2-normalized (as produced by
    ``build_index``); only the query vector is normalized here. A single
    normalized-matrix-vector product then gives cosine similarity for every
    candidate at once.
    """
    if index.embeddings.shape[0] == 0:
        return []

    norm = np.linalg.norm(query_embedding)
    if norm == 0:
        return []
    normalized_query = (query_embedding / norm).astype(np.float32)

    scores = index.embeddings @ normalized_query  # (N,) cosine similarities
    order = np.argsort(-scores)
    return [(index.entries[i], float(scores[i])) for i in order]
