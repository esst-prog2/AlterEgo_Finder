## Context

Greenfield: no source code exists yet, only README.md's spec and the
capability contracts in this change's specs/. The project must run on
Windows with a simple `pip install` (a course grader will run it, not just
the author), and README section 5 commits to running "entirely offline
without uploading images anywhere." See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Implement the `face-embedding` and `face-matching-cli` capabilities as
  specified.
- Keep the query path fast (README's 100ms end-to-end demo) via a single
  vectorized similarity computation, not a per-candidate Python loop.

**Non-Goals:**
- Threshold-based confidence labels (`HIGH_CONFIDENCE`/etc.) — depends on
  the calibrated threshold from the next change.
- `summary.html` report generation — a later change.
- Re-deriving or validating the specific value `0.68` — that number belongs
  to the calibration change and is not referenced here.

## Decisions

### Detection + embedding: OpenCV DNN (SSD) + OpenFace nn4.small2.v1
Chosen over `face_recognition`/dlib because dlib has no official Windows pip
wheel (needs CMake + Visual C++ Build Tools), which is a real barrier for a
grader running this on Windows. OpenCV's `opencv-python` ships prebuilt
wheels and its DNN module runs both the face detector (Caffe SSD,
res10_300x300) and the OpenFace embedding model. Both models output a
128-d vector, matching the project's stated shape. InsightFace/ArcFace was
rejected because it outputs 512-d, breaking that contract.

### Model weights are vendored in the repo, not downloaded at runtime
The detector (~10MB) and embedding model (~30MB) weight files are checked
into the repo (e.g. under `models/`) rather than fetched on first run.
Alternative considered: download-on-first-use. Rejected because it adds a
network dependency and a new failure mode to a tool whose README explicitly
markets running "entirely offline" as a privacy mitigation — a one-time
~40MB of vendored weights is an acceptable trade for keeping that claim
true and the setup deterministic. Source URLs for the weights are recorded
in `models/README.md` in case they need to be re-vendored.

### Module layout
- `match.py` — CLI entrypoint (arg parsing, orchestration, error handling).
- `face_pipeline/detector.py` — OpenCV DNN face detector wrapper.
- `face_pipeline/embedder.py` — OpenFace embedding wrapper.
- `face_pipeline/index.py` — dataset indexing, `.npy` cache read/write,
  staleness check, vectorized cosine similarity.

This separates the reusable embedding primitive (`detector.py` +
`embedder.py`, matching the `face-embedding` capability) from the CLI-only
indexing/matching logic, since the calibration change's `calibrate.py` will
need to reuse the embedding primitive without depending on `match.py`.

### Similarity computation
Embeddings are L2-normalized once, at both index-build time and query time.
Cosine similarity for all candidates then reduces to a single normalized
matrix-vector dot product (BLAS-backed via numpy), matching README's
"vectorized matrix multiplication" requirement without a per-candidate loop.

### Cache staleness check
The `.npy` index is written alongside a small sidecar JSON manifest listing
each indexed file's relative path, size, and mtime. On each run, the current
directory listing is compared against the manifest; any difference triggers
a full rebuild. This satisfies the "cache reused if fresh / rebuilt if
stale" spec scenarios without needing a heavier content hash.

## Risks / Trade-offs

- [Risk] The OpenCV+OpenFace embedding space may not behave identically to
  dlib's, so README's example threshold (0.68) may not transfer to this
  model pairing. → Mitigation: this change never hardcodes 0.68 — the
  calibration change derives the real threshold against whichever model is
  actually used.
- [Risk] Vendoring ~40MB of model weights bloats the git repo. → Mitigation:
  acceptable one-time cost for a course project; source URLs are documented
  for re-vendoring if needed.
- [Risk] LFW person-name folders can contain non-ASCII characters. →
  Mitigation: use `pathlib` and UTF-8 handling throughout; not expected to
  be a major issue at this dataset's scale.

## Open Questions

- Exact staleness-check encoding (e.g. which fields go in the manifest
  beyond path/size/mtime) may be refined during implementation without
  changing the spec's cache-reused/cache-rebuilt contract.
