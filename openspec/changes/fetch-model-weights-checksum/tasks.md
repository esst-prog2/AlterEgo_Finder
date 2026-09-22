## 1. Manifest and weights module

- [x] 1.1 Create `models/manifest.json` with the two current model
  entries (filename, url, sha256), matching the values already recorded
  in `models/README.md`; verify it's valid JSON and both checksums match
  the currently-vendored local files.
- [x] 1.2 Implement `face_pipeline/weights.py`'s `ensure_weight(filename)`:
  return the local path immediately if it exists and passes checksum;
  otherwise download to a `.part` temp file, verify, rename into place;
  verify a unit test for the already-present-and-valid path (no download
  attempted).
- [x] 1.3 Implement `ModelWeightError` and the checksum-mismatch failure
  path; verify a unit test with a deliberately corrupted local file
  raises `ModelWeightError` and does not return a path to load.
- [x] 1.4 Implement the download-failure path; verify a unit test
  (network calls mocked, not hitting a real bad URL) confirms a failed
  download raises `ModelWeightError` naming the file, keeping the test
  suite network-independent.

## 2. Integration

- [x] 2.1 Wire `detector.py`'s `_get_detector()` to call
  `ensure_weight(...)` before `cv2.FaceDetectorYN.create(...)`; verify
  existing detector tests still pass.
- [x] 2.2 Wire `embedder.py`'s `_get_net()` to call `ensure_weight(...)`
  before `cv2.dnn.readNetFromONNX(...)`; verify existing embedder tests
  still pass.
- [x] 2.3 Manually verify the real download path end to end: temporarily
  move a local model file aside, run the pipeline, confirm it
  re-downloads, checksum-verifies, and produces a working
  detector/embedder; restore or keep the re-downloaded file. Not an
  automated test (keeps the suite network-independent), but confirms the
  mocked unit tests reflect real behavior. Both files (YuNet, ArcFace
  INT8) re-downloaded successfully in ~22s total, byte-identical to the
  originals (checksums verified), and the full calibrate.py -> match.py
  pipeline produced identical results to before.

## 3. Git hygiene

- [x] 3.1 Add `models/*.onnx` to `.gitignore`; `git rm --cached` the two
  currently-tracked files; verify `git status` shows them as untracked
  (present on disk, no longer staged for tracking).
- [x] 3.2 Update `models/README.md` to describe fetch-on-first-run plus
  checksum-verified-on-every-use, referencing `models/manifest.json`
  instead of duplicating the hash values in prose; verify the doc no
  longer describes the files as vendored/manually-re-downloaded.

## 4. Verification

- [x] 4.1 Run the full scenario set from
  `specs/model-weight-delivery/spec.md` plus the entire project test
  suite and confirm all pass; verify via the test runner's summary output
  showing zero failures. 37/37 passing.
