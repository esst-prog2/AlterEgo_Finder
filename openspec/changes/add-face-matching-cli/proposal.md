## Why

The project has a written spec (README.md) but no code yet. Before calibration
(threshold tuning) or reporting can be built, the project needs a working core:
given a query photo and a dataset of face images, produce ranked candidate
matches by identity similarity. This change delivers that core end-to-end.

## What Changes

- Add face detection + 128-d embedding extraction using OpenCV's DNN module:
  a Caffe SSD detector (res10_300x300) for face localization, followed by the
  OpenFace `nn4.small2.v1` model for the 128-d embedding.
- Add automatic indexing of `data/celebrities/` (LFW-style layout, one
  subfolder per person) into a cached `.npy` embedding matrix, built on first
  run.
- Add the `match.py` CLI: takes `--image` (query photo) and `--dataset`
  (target directory), extracts the query embedding, computes vectorized
  cosine similarity against the cached index (matrix product, no per-file
  Python loop), and prints ranked candidate matches (person name + score) to
  stdout.
- Add explicit handling for images with no detectable face: exit code 1,
  message `Error: No face detected in input image`.
- **Out of scope for this change**: threshold-based confidence classification
  (`HIGH_CONFIDENCE` / `LOW_CONFIDENCE` / `NO_MATCH`) — that requires the
  calibrated threshold from the next change. This change only ranks and
  prints raw similarity scores.
- **Out of scope for this change**: the `summary.html` report — a later
  change.

## Capabilities

### New Capabilities
- `face-embedding`: detect a single face in an image and extract a 128-d
  embedding vector. A shared primitive — also consumed by the calibration
  change's `calibrate.py`.
- `face-matching-cli`: CLI that auto-indexes a dataset directory into a
  cached embedding matrix and ranks candidate matches for a query image by
  cosine similarity.

### Modified Capabilities
None — no existing specs in this project yet.

## Impact

- New Python modules: a `match.py` entrypoint plus supporting modules for
  detection, embedding, and indexing.
- New dependency: `opencv-python` (DNN module) and `numpy`. No other ML
  dependency (no dlib/torch/tensorflow).
- New pretrained model files bundled or fetched: the OpenCV face-detector
  weights (`res10_300x300_ssd_iter_140000.caffemodel` + `deploy.prototxt`)
  and the OpenFace `nn4.small2.v1` embedding model.
- New cached artifact: the `.npy` embedding matrix for `data/celebrities/`,
  including a staleness check so a changed dataset doesn't silently match
  against a stale cache.
