## Why

A photo turned by 90, 180 or 270 degrees does not reliably give "No face detected". Measured on
150 LFW people: an upside-down photo still "finds" a face 97 times of 150, and the embedding is
garbage (median same-person score -0.005, none reaching *Same person*). The page then shows ten
ordinary-looking cards that mean nothing. For a tool whose point is that its answers can be
trusted, a wrong answer that looks right is worse than an error.

The obvious fix, retrying only when no face is found, misses this, since a face was found. But
the detector's own confidence tells the orientations apart: on 300 upright LFW photos, upright
scored highest of the four every time, by at least 0.024 over upside-down.

## What Changes

- **Detection checks all four orientations,** and turns the photo only if another one clearly
  beats upright. The face's box and landmarks are mapped back, so alignment works as before.
- **Upright photos take today's exact path,** so their results stay byte-identical. If any existing
  dataset image turns, that is examined before going on.
- **Plain tilts are not addressed.** Up to 20 degrees they already work, 30 is weaker, and 45 stays
  poor (31 of 150 reach *Same person*). The limit is stated.

Not changing: thresholds, the page, the CLI's output, README's demo and its numbers.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `face-embedding`: "Face detection and embedding extraction" gains the orientation rule and its
  scenarios.

## Impact

- `face_pipeline/detector.py` and `tests/test_detector.py`. No new dependencies.
- A few more detector passes per image, on a small copy. The index build time is measured.
