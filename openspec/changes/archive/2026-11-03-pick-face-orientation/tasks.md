## 1. Tests first

- [x] 1.1 Log D5's expectations in PLANNING_LOG.md before any result exists
- [x] 1.2 Write tests in `tests/test_detector.py`: a fixture face turned 90, 180 and 270 degrees is found, with box and landmarks in the supplied image's coordinates and inside it, and an embedding close to the upright one; an upright photo gives exactly the old result; a turned score within the margin does not turn; upright found only at full size does not turn (D3); a blank image gives None; the large-face and shirt-print tests still pass. See them fail, on the real behaviour

## 2. The fix

- [x] 2.1 Implement the orientation check and mapping back in `face_pipeline/detector.py` (D1, D3, D4), and verify the tests
- [x] 2.2 Mutation-check: no margin, skipping D3, not mapping landmarks back, and deciding on the wrong copy must each fail a test
- [x] 2.3 Run the choice over every image we have (LFW, the pool, fixtures, the spike's photos, the private test photos), and report which turn, without showing or naming anyone in a private photo. Adjust the margin if needed, and record the final value

## 3. Proof and record

- [x] 3.1 Repeat the rotation table with the fix, for 0, 10, 20, 30, 45, 60, 90, 135, 180 and 270 degrees, and compare with D5, including anything wrong
- [x] 3.2 Verify nothing else moved: embeddings for `data/celebrities` and `data/wikidata` and LFW calibration are byte-identical, and the demo gives Psy 0.2702, `Me_PK` 0.4322 and "No face detected"
- [x] 3.3 Measure the cost: index build time before and after, and false faces on non-face images (a new, larger set: the images `detect-large-faces` used are no longer on this machine)
- [x] 3.4 In Chromium, on a separate port: `PK.jpg` turned upside down gets the same top match as upright, and the page's face crop is straight. Confirm no private photo is tracked
- [x] 3.5 State the 45 degree limit in README if it has a place for limits, update AGENTS.md and the skill's test counts, verify `pytest` in full and with Streamlit hidden, and append the outcome to PLANNING_LOG.md
