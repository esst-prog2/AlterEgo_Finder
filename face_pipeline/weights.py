"""Downloads and checksum-verifies vendored model weight files on demand.

Model files are no longer tracked in git (see models/manifest.json for
their source URLs and expected SHA-256 checksums); this module fetches
them to models/ on first use and re-verifies the checksum on every use,
whether the file was just downloaded or already present locally.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MANIFEST_PATH = MODELS_DIR / "manifest.json"

_CHUNK_SIZE = 1 << 20  # 1 MiB


class ModelWeightError(Exception):
    """Raised when a model weight file can't be obtained or verified."""


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    """Download to a .part sibling file, then rename into place, so a
    failed or interrupted download never leaves a file at ``destination``
    for a later run to mistakenly trust.
    """
    part_path = destination.with_name(destination.name + ".part")
    try:
        urllib.request.urlretrieve(url, part_path)
    except (urllib.error.URLError, OSError) as exc:
        part_path.unlink(missing_ok=True)
        raise ModelWeightError(
            f"Failed to download model weight file {destination.name} from {url}: {exc}"
        ) from exc
    part_path.replace(destination)


def ensure_weight(filename: str) -> Path:
    """Return a local, checksum-verified path for ``filename``.

    Downloads it first if not already present. Raises ``ModelWeightError``
    if the download fails or the checksum doesn't match; a mismatched file
    is removed so the next run re-downloads rather than repeatedly failing
    on a known-bad local copy.
    """
    manifest = _load_manifest()
    if filename not in manifest:
        raise ModelWeightError(f"No manifest entry for model weight file: {filename}")

    entry = manifest[filename]
    destination = MODELS_DIR / filename

    if not destination.exists():
        _download(entry["url"], destination)

    actual = _sha256(destination)
    if actual != entry["sha256"]:
        destination.unlink(missing_ok=True)
        raise ModelWeightError(
            f"Checksum mismatch for {filename}: expected {entry['sha256']}, "
            f"got {actual}. The file has been removed; re-run to re-download."
        )

    return destination
