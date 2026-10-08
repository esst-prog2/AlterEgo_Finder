## 1. Test first

- [x] 1.1 Log the expected values in PLANNING_LOG.md before writing the tests: (a) on PK.jpg the detected box's centre lies in the user's head region (x 220-390, y 225-440, read by eye); (b) of a 40x54 box scoring 0.95 and a 134x171 box scoring 0.90, the 134x171 box is picked
- [x] 1.2 Copy data/my_photo/PK.jpg to tests/fixtures/ and add both tests to tests/test_detector.py; verify they fail before implementation

## 2. Implementation

- [x] 2.1 In face_pipeline/detector.py, lower SCORE_THRESHOLD to 0.8 and add pick_largest_face(), used by detect_face(); verify both new tests and the existing detector tests pass
- [x] 2.2 Run the full test suite and the run-alterego-finder driver; verify both pass

## 3. Verification

- [x] 3.1 Red/green: change pick_largest_face back to returning the top-scoring row and verify the planted-answer test fails; restore and verify all tests pass; log both runs
- [x] 3.2 Re-run step 6: delete data/celebrities/.matchcache, re-run calibrate.py and match.py on data/my_photo/PK.jpg; log the result against the expectation already logged for step 6
