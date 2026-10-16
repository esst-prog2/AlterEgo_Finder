## 1. Test first

- [x] 1.1 Log the expected values in PLANNING_LOG.md before writing the tests: on a 12-image dataset (fixture images copied under 12 person folders), the default run prints exactly 10 lines, the 10 highest scores of a `--top 12` run in the same order; `--top 3` prints 3 lines; `--top 0` exits 2
- [x] 1.2 Add those tests to tests/test_match_cli.py; verify they fail before implementation

## 2. Implementation

- [x] 2.1 In match.py, add `--top` (default `REPORT_TOP_K`, rejects values below 1) and print only the first N labeled results; verify the new tests and all existing tests pass

## 3. Verification

- [x] 3.1 Red/green: remove the slice so every candidate is printed, verify the default-cap test fails; restore, verify all tests pass; log both runs
- [x] 3.2 Run match.py on data/my_photo/PK.jpg against data/celebrities and verify it prints 10 lines (was 500); log the result
