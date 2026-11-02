## Why

Real phone photos with an obvious face get "No face detected". YuNet scores very large
faces lower: two photos scored 0.798 and 0.58 at full size against the 0.8 cutoff, but
0.83 and 0.81 on a 1600-pixel copy. Recent phone photos are what people will actually
try, so this would fail in front of the people the program is for.

## What Changes

- When no face is found at full size, detection retries on copies whose longest side is
  1600, 1024 and 640 pixels, using only sizes smaller than the image, and stops at the
  first one that finds a face.
- The box and landmarks are mapped back to the full-size image, so the face crop and the
  embedding still come from the full-quality photo.
- Nothing else changes: an image with a face found at full size gets exactly the same
  result, so LFW, its thresholds and README's scores stay the same.

**Not in this change:** rotating images. A strongly tilted face can still be missed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `face-embedding`: "Face detection and embedding extraction" retries on smaller copies.

## Impact

- Changed: `face_pipeline/detector.py`, `tests/test_detector.py`.
- Everything that detects faces gains the retry: the CLI, the page, calibration, indexing
  and the pool build.
- No new dependencies. A large photo with no face takes up to four detection passes, not
  one.
