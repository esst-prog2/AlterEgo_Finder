## 1. Setup

- [x] 1.1 Create the Python package structure (`match.py`,
  `face_pipeline/__init__.py`, `detector.py`, `embedder.py`, `index.py`) and
  a `requirements.txt` (`opencv-python`, `numpy`); verify
  `pip install -r requirements.txt` followed by
  `python -c "import cv2, numpy"` succeeds.
- [x] 1.2 Add a `models/` directory with a `README.md` documenting the
  source URLs and expected filenames for both weight files; verify the file
  lists both.

## 2. Model weights

- [x] 2.1 Vendor the OpenCV face-detector weights
  (`res10_300x300_ssd_iter_140000.caffemodel` + `deploy.prototxt`) into
  `models/`; verify `cv2.dnn.readNetFromCaffe(...)` loads them without error.
- [x] 2.2 Vendor the OpenFace `nn4.small2.v1` embedding model into
  `models/`; verify `cv2.dnn.readNetFromTorch(...)` loads it without error.

## 3. face-embedding capability

- [x] 3.1 Implement `face_pipeline/detector.py` wrapping the OpenCV DNN face
  detector, returning a bounding box or `None`; verify a unit test on a
  known-face fixture image returns a box, and on a no-face fixture image
  returns `None`.
- [x] 3.2 Implement `face_pipeline/embedder.py` producing a 128-d vector
  from a detected face crop; verify a unit test asserts output shape
  `(128,)` and that running it twice on the same image yields identical
  vectors (embedding determinism scenario).
- [x] 3.3 Implement `extract_embedding(image)` combining detection +
  embedding, returning an embedding or a distinct "no face" result; verify
  unit tests cover both the face-present and no-face-detected scenarios
  from `specs/face-embedding/spec.md`.

## 4. Dataset indexing and caching

- [x] 4.1 Implement dataset walking in `face_pipeline/index.py`:
  `data/celebrities/<person>/*.jpg` → an `(N, 128)` embedding matrix plus a
  parallel `(person, filepath)` label list; verify a unit test on a small
  fixture dataset produces a matrix with the expected row count.
- [x] 4.2 Implement `.npy` cache write plus a sidecar manifest (path, size,
  mtime per indexed file) after indexing; verify both files exist at the
  expected location after a first run on a fixture dataset.
- [x] 4.3 Implement the freshness check that compares the current directory
  listing against the manifest and reuses the cache when unchanged; verify
  a unit test confirms no re-indexing occurs on a second run with unchanged
  files (cache-reused-if-fresh scenario).
- [x] 4.4 Implement cache rebuild when the manifest and directory listing
  disagree; verify a unit test confirms a rebuild after adding/removing a
  file in the fixture dataset (cache-rebuilt-if-stale scenario).

## 5. Matching CLI

- [x] 5.1 Implement vectorized cosine similarity: L2-normalize the index
  matrix and the query embedding once, then compute similarity via a single
  matrix-vector product; verify a unit test checks scores against a
  hand-computed reference for a small fixture matrix.
- [x] 5.2 Implement `match.py` argument parsing for `--image` and
  `--dataset`; verify `python match.py --help` documents both flags.
- [x] 5.3 Wire the CLI to print ranked candidates (person name + score,
  most similar first) to stdout; verify an integration test running
  `match.py` against a fixture dataset with two photos of Person A and one
  of Person B ranks Person A above Person B with a higher score (correct
  identity ranking scenario; README section 4).
- [x] 5.4 Implement the no-face-detected CLI path: exit code 1 and
  `Error: No face detected in input image` on stdout/stderr; verify an
  integration test running `match.py` with a faceless query image asserts
  exit code 1 and the exact message (README section 4 / section 1).

## 6. Verification

- [x] 6.1 Run the full scenario set from `specs/face-embedding/spec.md` and
  `specs/face-matching-cli/spec.md` as automated tests and confirm all
  pass; verify via the test runner's summary output showing zero failures.
