## Context

Builds on the archived `add-face-matching-cli` and `add-threshold-calibration`
changes. See proposal.md for motivation, and PLANNING_LOG.md's 2026-09-22
entry ("Reopened the embedding-model choice...") for the reasoning behind
revisiting a decision both prior changes treated as settled.

## Goals / Non-Goals

**Goals:**
- Implement YuNet detection+landmarks, 5-point alignment, and ArcFace
  ResNet100 INT8 (512-d) embedding, satisfying the MODIFIED `face-embedding`
  spec.
- Preserve `extract_embedding(image) -> np.ndarray` / `NoFaceDetectedError`
  as `face_pipeline/embedder.py`'s external contract unchanged, so
  `index.py`, `match.py`, `calibrate.py`, and `face_pipeline/calibration.py`
  need zero code changes — they only care about "give me an embedding or
  tell me there's no face," not which model produced it.
- Retune any test that hardcodes a threshold value or score expectation
  tied to the old embedding model's similarity distribution.

**Non-Goals:**
- How the new model files are delivered (vendored vs. fetched-with-checksum)
  — `fetch-model-weights-checksum`'s concern.
- README's "128-d"/"0.68" text — also `fetch-model-weights-checksum`'s
  concern (per the agreed change split), even though it will read as
  briefly stale between this change landing and that one.

## Decisions

### Detector: YuNet via `cv2.FaceDetectorYN`
Officially bundled/documented in OpenCV's own model zoo
(`opencv/opencv_zoo`), ~227KB, one ONNX forward pass gives both the
bounding box and 5 facial landmarks — no separate landmark model, no new
dependency beyond `opencv-python` (same footprint as today).
`setInputSize()` must be called with the actual per-image dimensions
before each `detect()` call — YuNet's input size isn't fixed at model-load
time.

### Alignment: standard ArcFace 5-point reference template
Reference points for a 112×112 aligned output:
`[[38.2946,51.6963],[73.5318,51.5014],[56.0252,71.7366],[41.5493,92.3655],[70.7299,92.2041]]`.
Computed via `cv2.estimateAffinePartial2D` + `cv2.warpAffine`, a standard
technique, not something invented for this project.

**Landmark ordering — corrected during implementation**: research turned up
a prose description implying this reference array is in (left eye, right
eye, nose, left mouth corner, right mouth corner) order, the mirror of
YuNet's own (right eye, left eye, nose, right mouth corner, left mouth
corner) output order — suggesting the two needed explicit re-pairing.
That description was wrong (or at least misleading). Verified empirically
instead: fitting `estimateAffinePartial2D` through all 5 points and
checking the *residual* (not just whether the code runs) showed the
naive, direct index-for-index pairing between YuNet's output and this
reference array gives a tight fit (~2.6px mean residual across all 5
points); the "corrected" re-pairing this design originally called for
produced a ~20px mean residual and a visibly rotated, wrong alignment.
The lesson generalizes: for this kind of landmark-correspondence code, a
prose claim about point ordering is unverified until you fit a transform
and look at per-point error, not just "did it throw."

### Embedder: ArcFace ResNet100, INT8, via `cv2.dnn.readNetFromONNX`
Confirmed by user: INT8 (~63MB) over FP32 (~249MB), same ArcFace-family
512-d characteristics, far more reasonable to vendor now and fetch later.
Source: `onnxmodelzoo/arcfaceresnet100-8` on Hugging Face (the ONNX Model
Zoo's own GitHub LFS hosting was discontinued July 2025). No published
checksum exists for this specific file — its SHA-256 is computed after
downloading and recorded in `models/README.md`, the same as this project
already did for `res10_300x300_ssd_iter_140000.caffemodel`'s prototxt.

**Preprocessing — corrected during implementation, and this one mattered a
lot**: multiple sources (including one already cited above) describe this
model family's preprocessing as RGB, 112×112, `(pixel - 127.5) / 128.0`.
Implementing exactly that produced same-person and different-person
cosine similarities both clustered in the same ~0.94–0.98 band on this
project's fixtures — no usable separation, which would have made
calibration meaningless (there'd be no threshold that separates a match
from a non-match). Before assuming this was an INT8 quantization problem,
the FP32 model was downloaded and tested the same way: same collapse, if
anything slightly worse (0.94–0.98 vs INT8's 0.76–0.86) — ruling out
quantization as the cause and pointing at preprocessing instead. Testing
a small matrix of (mean, scale, RGB/BGR) combinations against the actual
fixtures found the real answer: **raw pixel values, RGB order, no mean
subtraction or scaling at all** — apparently this particular ONNX Model
Zoo export (an older MXNet-derived `LResNet100E-IR` conversion) expects
unnormalized input, unlike newer insightface model conventions. Result:
same-person ~0.7–0.8, different-person ~−0.09 to +0.07 — a clean,
well-separated distribution, and a real, substantial improvement over the
old 128-d pipeline's numbers (which had same/different pairs as close as
0.64 vs 0.71). The general lesson, same as the landmark-ordering one
above: a documented preprocessing recipe is a hypothesis, verified by
measuring actual same-person vs. different-person separation on real
photos, not by "the code runs without error."

### Recalibration is empirical, not a fixed number
Unlike `add-threshold-calibration`, this change doesn't hardcode any new
threshold value in the spec or design — the actual numbers depend on how
the new model's cosine-similarity distribution behaves on the test
fixtures, which can only be observed after the pipeline is implemented and
run. Tests with fixed threshold constants get updated during
implementation once real scores are observed, mirroring how a similar
issue (a test bug, not a pipeline bug) was caught and fixed empirically in
`add-face-matching-cli`.

## Risks / Trade-offs

- [Risk] Landmark-ordering mismatch (see above) produces plausible-looking
  but silently degraded alignment — the pipeline won't crash, embeddings
  will just be worse. → Mitigation: a unit test asserting the aligned
  output's eye positions land near the reference template's expected
  coordinates, not just "alignment ran without error."
- [Risk] INT8 quantization trades some accuracy for size. → Mitigation:
  explicit user decision; not expected to matter at this project's scale.
- [Risk] Previously-passing hardcoded-threshold tests will need new
  constants once real ArcFace scores are observed. → Mitigation: expected
  and intentional, not a regression — the whole point of recalibration.

## Migration Plan

Old vendored files (`deploy.prototxt`,
`res10_300x300_ssd_iter_140000.caffemodel`, `nn4.small2.v1.t7`) are removed
from `models/` and replaced. No data migration: a real `data/config.json`
from a prior run is now stale (wrong model's thresholds) and must be
regenerated by re-running `calibrate.py`.

## Open Questions

None blocking — retuned threshold constants are determined empirically
during implementation without changing the spec or approach.
