## Context

Measured in a temporary accented folder with OpenCV 4.14: `cv2.imread` returned nothing,
`cv2.imwrite` returned False, and `FaceDetectorYN.create` and `dnn.readNetFromONNX` both raised an
error from a path. Reading the same files through NumPy and passing bytes worked:
`cv2.imdecode`, `FaceDetectorYN.create("onnx", model, config, ...)` and `readNetFromONNX(bytes)`.
On a test image and one blob, the bytes route gave an identical detection and embedding.

The program never calls `cv2.imwrite`: reports and pool images are written from Python, which
handles any path. So only reads and model loads need changing.

`weights.py` uses `urllib.request.urlretrieve`, which has no timeout. `setup_data.py` already has
`DOWNLOAD_TIMEOUT_S = 60`, per network read, with `urlopen`.

## Goals / Non-Goals

**Goals:**
- Every read in the program works on any path, with identical results.
- A stalled weight download fails with the existing clear error.
- A regression cannot quietly return.

**Non-Goals:**
- Changing the pool's ASCII folder names, or the committed list. They are harmless, and changing
  them would force a rebuild for no gain.
- The throwaway spike scripts or the skill's driver. The tests' own image reads were a non-goal at
  first, but they stopped the suite running from an accented folder, so the user chose to fix them too.
- A total download time limit: the 63 MB model can legitimately take a while on a slow link.

## Decisions

### D1: One helper, `face_pipeline/images.py`

`read_image(path)` returns what `cv2.imread` did: a BGR array, or None if the file is missing or
not an image. It uses `np.fromfile` and `cv2.imdecode(..., cv2.IMREAD_COLOR)`. `np.fromfile` raises
on a missing file where `imread` returned None, so the helper catches `OSError`, keeping every
caller's existing error handling unchanged.

An empty file needs care too, since `imdecode` raises on an empty buffer, so that also gives None.

`imread` honours EXIF orientation, which phone photos depend on. `imdecode` should too. That is
checked on every image we have, not assumed (see D4).

### D2: Models load from bytes

`detector.py` and `embedder.py` read the checksum-verified file with `np.fromfile` and pass the
bytes to OpenCV. This keeps `ensure_weight` as it is, so the checksum still covers the file used.

### D3: The download uses `urlopen` with a timeout

`_download` streams through `urlopen(url, timeout=DOWNLOAD_TIMEOUT_S)` into the `.part` file. The
timeout is per read, so a slow but moving download still finishes. `socket.timeout` is an `OSError`,
so the existing handler removes the partial file and raises `ModelWeightError`. A stall mid-file is
what this fixes, and the checksum still catches anything truncated.

### D4: Proof that results did not move

- `read_image` equals `cv2.imread` pixel for pixel on every image under `data/` and `tests/fixtures`,
  including the phone photos with EXIF orientation.
- Rebuilt embeddings for `data/celebrities` and `data/wikidata` are byte-identical to their caches,
  and calibration is byte-identical to `data/config.json`.
- The test suite runs from a real copy of the repository in an accented folder, and in Chromium the
  page matches `PK.jpg` there, with Psy at 0.2702.

### D5: A guard against regressions

A test scans the program's own files for `cv2.imread(` and for models loaded from a path, so a new
call fails the suite on any machine, including one where such a path would never come up.

## Risks / Trade-offs

- **A model's bytes stay in memory only while loading.** Loading happens once per run, so this is a
  brief extra 63 MB.
- **Other libraries could fail on such a path.** The copy in an accented folder is what would show it,
  and Streamlit's page is checked there too.
- **The guard is a text scan,** so it can be fooled by an alias. That is fine for a course project.
