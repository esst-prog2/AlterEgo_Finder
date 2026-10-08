## 1. Test first

- [x] 1.1 Log the expected value (at most 1% of absent strangers HIGH_CONFIDENCE against a 500-face index; from the spec's target FAR and the spike's 198/200) in PLANNING_LOG.md before writing the test; verify the log line precedes the test
- [x] 1.2 Write tests/test_index_size_threshold.py (synthetic 500-face index, 200 calibration strangers, 200 disjoint query strangers) and verify it fails before implementation

## 2. Implementation

- [x] 2.1 Add top1_scores and compute_index_high_threshold to face_pipeline/calibration.py; verify tests/test_index_size_threshold.py passes
- [x] 2.2 calibrate.py: required --dataset, fit threshold_high against get_or_build_index(dataset), clamp to threshold_low; verify tests/test_calibrate_cli.py passes with --dataset
- [x] 2.3 Add a test for the spec scenario "High threshold grows with index size" (nested indices, same strangers); verify it passes

## 3. Docs and tooling

- [x] 3.1 Update README section 3 and the run-alterego-finder SKILL.md/driver.py; verify the driver passes end to end

## 4. Verification

- [x] 4.1 Red/green: change `.max(axis=1)` to `[:, 0]` in top1_scores and verify the test fails; restore and verify all 44 tests pass; both runs logged in PLANNING_LOG.md
- [x] 4.2 Use the program for real on an absent-stranger photo against a real dataset; log the expectation in PLANNING_LOG.md first, then the observed output
