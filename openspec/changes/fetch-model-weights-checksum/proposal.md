## Why

`models/arcfaceresnet100-11-int8.onnx` (63MB) already triggered a GitHub
warning on push for exceeding their recommended 50MB file size, and
vendoring binary weights means every clone of this repo pays for ~63MB it
may never need to re-download. Fetch-with-checksum removes the binaries
from git tracking while keeping the same integrity guarantee: a SHA-256
check before the weights are trusted for inference.

## What Changes

- Add a small model-delivery module: given a model's expected filename,
  source URL, and SHA-256, it downloads the file to `models/` if not
  already present, verifies the checksum, and raises a clear error if the
  download fails or the checksum doesn't match — never silently loading
  unverified weights.
- `face_pipeline/detector.py` and `face_pipeline/embedder.py` call this
  before loading their respective nets, instead of assuming the file is
  already on disk.
- Remove `models/*.onnx` from git tracking and add them to `.gitignore`.
- Update `models/README.md` to describe the fetch-on-first-run + checksum
  behavior, replacing the current "vendored, re-download manually if
  needed" framing.

## Capabilities

### New Capabilities
- `model-weight-delivery`: automatic download-if-missing plus SHA-256
  verification for the project's ONNX model files, with a clear failure
  mode instead of silently proceeding on a bad or missing file.

### Modified Capabilities
None — `face-embedding`'s detect/embed behavior is unchanged; it simply
now depends on model files becoming available through a different
delivery mechanism, which is an implementation detail, not an externally
visible behavior change to that capability.

## Impact

- New module: `face_pipeline/weights.py` (download-if-missing + SHA-256
  verify).
- `face_pipeline/detector.py`, `face_pipeline/embedder.py`: call into it
  before `cv2.FaceDetectorYN.create(...)` / `cv2.dnn.readNetFromONNX(...)`.
- `.gitignore`: add the vendored `.onnx` files.
- Git history: `git rm --cached` the two currently-tracked model files
  (they stay on disk locally; this only stops future commits from
  tracking them).
- `models/README.md`: rewritten to describe fetch-on-first-run.
- First run against a clean checkout now requires network access to
  download ~63MB; subsequent runs reuse the cached local files exactly as
  today.
