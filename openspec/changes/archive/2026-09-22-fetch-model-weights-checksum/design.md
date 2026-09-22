## Context

Builds on the archived `add-face-matching-cli` and `switch-to-arcface-embedding`
changes, which vendored `models/*.onnx` directly in git. See proposal.md for
motivation (a real GitHub file-size warning on the 63MB ArcFace weights).

## Goals / Non-Goals

**Goals:**
- Implement `model-weight-delivery`: download-if-missing + SHA-256 verify
  for both current model files (YuNet, ArcFace INT8), with a clear failure
  mode.
- Remove the binaries from git tracking without changing
  `detect_face`/`extract_embedding`'s external behavior.

**Non-Goals:**
- Changing which models are used (that's `switch-to-arcface-embedding`'s
  concern, already done).
- A general-purpose plugin/registry system for arbitrary future models —
  this is sized for the two files this project actually has.

## Decisions

### Single source of truth: `models/manifest.json`
A small JSON file mapping filename to `{url, sha256}`:
```json
{
  "face_detection_yunet_2023mar.onnx": {"url": "...", "sha256": "..."},
  "arcfaceresnet100-11-int8.onnx": {"url": "...", "sha256": "..."}
}
```
`face_pipeline/weights.py` reads this at runtime; `models/README.md`
references it instead of duplicating the exact hash strings in prose,
removing the risk of the two drifting apart on a future model update.

### Download mechanism: stdlib only
`urllib.request`, not `requests` — no new dependency, consistent with this
project's existing footprint (`opencv-python` + `numpy` only). Streamed to
a `.part` temp file alongside the destination, checksummed, then renamed
into place — a failed or interrupted download never leaves a corrupt file
at the real path for a later run to mistakenly trust.

### Checksum verified on every use, not just after downloading
Per the spec's "Checksum verification before use" requirement: an
already-present local file is re-verified too, not just a freshly
downloaded one. This guards against a corrupted or tampered-with local
copy being silently trusted just because it exists. Cost: hashing a 63MB
file with `hashlib.sha256` takes a fraction of a second — negligible next
to model loading and inference themselves, and this only runs once per
process (models are loaded once via the existing `_get_net()`/
`_get_detector()` lazy-singleton pattern), not per query.

### `face_pipeline/weights.py`'s interface
```python
def ensure_weight(filename: str) -> Path:
    """Return a local, checksum-verified path for `filename`,
    downloading it first if necessary. Raises ModelWeightError on
    checksum mismatch or download failure."""
```
`detector.py` and `embedder.py` call this in place of directly
constructing `MODELS_DIR / "<filename>"`, before passing the path to
`cv2.FaceDetectorYN.create(...)` / `cv2.dnn.readNetFromONNX(...)`. A
single `ModelWeightError` exception covers both failure modes named in
the spec (download failure, checksum mismatch) — proportionate to two
files and two failure conditions, not split into a larger exception
hierarchy.

### Git history
`git rm --cached` the two currently-tracked `.onnx` files and add
`models/*.onnx` to `.gitignore`. The files stay on disk locally (no need
to force a re-download during this change's own development/testing), but
stop being tracked going forward.

## Risks / Trade-offs

- [Risk] First run on a clean checkout now needs network access (~63MB
  download) where it didn't before. → Accepted trade-off, explicit
  motivation for this change; `models/README.md` states it plainly.
- [Risk] If the upstream Hugging Face / GitHub source URLs ever change or
  go offline, `ensure_weight` fails clearly (per spec) rather than
  degrading silently, but there's no fallback mirror. → Acceptable for
  this project's scope; the failure is loud and actionable, not silent.

## Migration Plan

No data migration. Existing local `models/*.onnx` files (from prior
changes) remain valid — checksum verification will pass against them
unchanged, so a developer with an existing checkout doesn't need to
re-download anything.
