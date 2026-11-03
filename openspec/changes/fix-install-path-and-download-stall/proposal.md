## Why

The program fails on anyone whose path has an accented letter, such as `C:\Users\György\...`,
which is plausible for classmates in Hungary. Measured with OpenCV 4.14 in a temporary accented
folder: both model files fail to load with an error, `cv2.imread` silently returns nothing, and
`cv2.imwrite` silently writes nothing. So the program stops at startup, and images in such a
folder cannot be read. Separately, the model weight download has no timeout, so a stalled
connection hangs for good on a first run, with no message.

## What Changes

- **Images are read from bytes** through one helper in the program's code, which works on any
  path, in place of each `cv2.imread` in `app.py`, `match.py` and `face_pipeline/`.
- **Both models are loaded from bytes,** so their paths never reach OpenCV.
- **The model weight download gets a timeout per network read,** as `setup_data.py`'s LFW
  download already has. A stall removes the partial file and gives the existing clear error.
- **Printing a name or path the console cannot show no longer crashes the CLIs.** Found while testing.
- **The tests read and write their images the same safe way,** so the suite also runs from such a folder. Added during implementation, at the user's choice, with a fix for tests that assumed an earlier run's cache.
- **Docs:** AGENTS.md and the skill no longer say a non-ASCII path breaks reading.

Not changing: results, which must stay byte-identical; the pool's ASCII folder names, which the
committed list already uses; and `spike_eval.py` and `spike_multiphoto.py`, which are throwaway.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-setup`: a new requirement that the program works from any install folder.
- `model-weight-delivery`: "Clear failure on download error" gains a stalled-download scenario.

## Impact

- New: `face_pipeline/images.py` (the helper). Changed: `app.py`, `match.py`,
  `face_pipeline/calibration.py`, `index.py`, `report.py`, `detector.py`, `embedder.py`,
  `weights.py`, and their tests. No new dependencies.
