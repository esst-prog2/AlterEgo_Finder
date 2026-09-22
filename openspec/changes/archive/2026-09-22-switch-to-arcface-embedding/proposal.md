## Why

The current 128-d embedding (OpenCV DNN detector + OpenFace `nn4.small2.v1`)
scores ~93% on the LFW verification benchmark. That model choice came from
`add-face-matching-cli`'s design.md treating README's illustrative "128-d"
mention as a hard contract — it never was one; nothing in README section 4's
acceptance criteria depends on embedding dimensionality. An ArcFace-family
model (512-d) scores 99%+ on the same benchmark, which more directly serves
the project's actual goal: correctly distinguishing identities.

## What Changes

- Replace the face detector with **YuNet** (`face_detection_yunet_2023mar.onnx`),
  OpenCV's own officially bundled/documented detector, loaded via
  `cv2.FaceDetectorYN`. One forward pass yields both the bounding box and 5
  facial landmarks.
- Add a **face-alignment step**: warp the detected face to a canonical
  112×112 pose using the standard ArcFace 5-point reference template, before
  embedding. The current pipeline has no alignment step; this is required
  for an ArcFace-family model to perform as expected.
- Replace the embedder with **ArcFace ResNet100, INT8-quantized** (512-d
  output) via `cv2.dnn.readNetFromONNX`.
- **MODIFIED**: `face-embedding`'s requirements change from 128-d to 512-d.
- **Recalibration**: threshold values are tied to the specific embedding
  model's similarity distribution. All threshold-dependent tests (fixed
  classification-boundary values, fixture-set assertions) are re-tuned
  against the new model's actual score distribution — the numbers from
  `add-threshold-calibration` are void once the embedding model changes,
  though the calibration *mechanism* (`calibrate.py`,
  `face_pipeline/calibration.py`) needs no code changes, since it's
  dimension-agnostic.
- **Out of scope for this change**: how the new model files are delivered
  (vendored vs. fetched). This change vendors them directly, same as
  `add-face-matching-cli` originally did — asset delivery is
  `fetch-model-weights-checksum`'s concern, kept separate to keep this
  change's diff reviewable.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `face-embedding`: the embedding output dimensionality changes from 128-d
  to 512-d (both the "Face detection and embedding extraction" and
  "Embedding determinism" requirements reference the vector size).

## Impact

- `face_pipeline/detector.py` replaced: YuNet via `cv2.FaceDetectorYN`
  (bbox + 5 landmarks), not the Caffe SSD detector.
- New `face_pipeline/alignment.py`: 5-point affine warp to a 112×112
  canonical pose.
- `face_pipeline/embedder.py` replaced: ArcFace ResNet100 INT8 via
  `cv2.dnn.readNetFromONNX`, not OpenFace.
- New vendored model files: `face_detection_yunet_2023mar.onnx` (~227KB),
  `arcfaceresnet100-11-int8.onnx` (~63MB) — replacing
  `deploy.prototxt`/`res10_300x300_ssd_iter_140000.caffemodel`/
  `nn4.small2.v1.t7`.
- `calibrate.py`, `face_pipeline/calibration.py`, `face_pipeline/index.py`,
  `match.py`: no code changes (dimension-agnostic), but tests with
  hand-tuned threshold constants or `(128,)` shape assertions need updating.
