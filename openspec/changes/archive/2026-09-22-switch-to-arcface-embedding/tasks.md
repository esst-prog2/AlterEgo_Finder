## 1. Model files

- [x] 1.1 Vendor `face_detection_yunet_2023mar.onnx` into `models/`; verify
  `cv2.FaceDetectorYN.create(...)` loads it without error.
- [x] 1.2 Vendor `arcfaceresnet100-11-int8.onnx` into `models/`; verify
  `cv2.dnn.readNetFromONNX(...)` loads it without error, and record its
  computed SHA-256 in `models/README.md`.
- [x] 1.3 Remove the old vendored files (`deploy.prototxt`,
  `res10_300x300_ssd_iter_140000.caffemodel`, `nn4.small2.v1.t7`) and their
  `models/README.md` entries; verify they no longer exist.

## 2. Detector (YuNet)

- [x] 2.1 Implement `face_pipeline/detector.py`'s detection using
  `cv2.FaceDetectorYN`, returning a bounding box plus 5 landmarks (or
  `None`); verify unit tests: a known-face fixture returns a box and 5
  landmarks, a no-face fixture returns `None`.
- [x] 2.2 Call `setInputSize()` with each image's actual dimensions before
  detection (YuNet's input size isn't fixed at load time); verify a unit
  test with two differently-sized fixture images both detect correctly.

## 3. Alignment

- [x] 3.1 Implement `face_pipeline/alignment.py`: warp a detected face to
  a 112×112 canonical pose using the ArcFace reference template via
  `cv2.estimateAffinePartial2D`/`cv2.warpAffine`. Corrected during
  implementation: YuNet's landmark order maps directly (index-for-index)
  onto the reference template, verified empirically via fit residual —
  the "explicit re-pairing" this task originally called for was based on
  a misleading source and produced a visibly wrong, rotated alignment
  (see design.md). Verify a unit test asserts the output is a valid
  112×112×3 image.
- [x] 3.2 Add a landmark-ordering regression guard: verify a unit test
  checks the aligned output's eye positions land near the reference
  template's expected coordinates within a tolerance, written so it would
  fail if the landmark pairing were swapped (i.e. it would have caught
  the bug found while implementing 3.1).

## 4. Embedder (ArcFace)

- [x] 4.1 Implement `face_pipeline/embedder.py`'s embedding step using the
  aligned crop and the ArcFace ONNX net, returning a 512-d vector; verify
  a unit test asserts output shape `(512,)`. Preprocessing resolved
  empirically, not from docs: the commonly-cited `(px-127.5)/128`
  normalization collapsed same/different-person similarity into the same
  ~0.94-0.98 band (confirmed on both INT8 and FP32 — not a quantization
  issue); raw, unnormalized RGB pixels give clean separation (same-person
  ~0.7-0.8, different-person ~-0.09 to +0.07). See design.md.
- [x] 4.2 Preserve `extract_embedding(image)` / `NoFaceDetectedError` as
  the module's external contract (detect -> align -> embed); verify the
  face-present and no-face-detected scenarios from
  `specs/face-embedding/spec.md` still pass.
- [x] 4.3 Verify embedding determinism (same image twice -> identical
  vector) with a unit test.

## 5. Downstream regression and recalibration

- [x] 5.1 Update every `(128,)` shape assertion across the existing test
  suite to `(512,)`; verify all such tests pass against the new pipeline.
  (Both used `EMBEDDING_SIZE` as a variable already, so this was a
  constant-value change in embedder.py, not a per-test edit.)
- [x] 5.2 Observe actual similarity scores the new pipeline produces on
  the existing test fixtures, and retune every hardcoded threshold
  constant in tests (e.g. classification-boundary values in
  `test_match_cli_thresholds.py`) to real, observed values — not
  copy-pasted from the old model; verify all threshold-dependent tests
  pass. Found and fixed a stray, gitignored `.matchcache/` sitting inside
  `tests/fixtures/dataset/` from earlier manual testing, holding a stale
  128-d cache that `shutil.copytree` was silently copying into every
  test's tmp dir and causing a matmul dimension-mismatch crash. The
  existing hardcoded classification-boundary constants (0.65/0.73) still
  pass correctly against the new pipeline's real scores (same-person
  ~0.7-0.8, different-person ~-0.09 to +0.07) without needing new values.
- [x] 5.3 Confirm the correct-identity-ranking and classification-label
  integration tests still pass end to end with the new pipeline; verify
  via test run.

## 6. Verification

- [x] 6.1 Run the full scenario set from the modified `face-embedding`
  spec, plus the entire project test suite, and confirm all pass; verify
  via the test runner's summary output showing zero failures. 33/33
  passing. Also ran the full driver end to end (calibrate.py -> match.py)
  as a holistic sanity check, not just unit tests.
