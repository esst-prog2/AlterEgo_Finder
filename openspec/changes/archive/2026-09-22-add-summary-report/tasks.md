## 1. Report rendering module

- [x] 1.1 Implement `face_pipeline/report.py`'s `render_report(query_image,
  results, output_path)`: base64-embed the query image and top-ranked
  candidates as JPEG data URIs, with color-coded confidence labels
  (`HIGH_CONFIDENCE`/`LOW_CONFIDENCE`/`NO_MATCH`); verify a unit test
  checks the output HTML contains embedded base64 image data and each
  rendered candidate's confidence label.
- [x] 1.2 Implement the `REPORT_TOP_K` cap; verify a unit test with more
  synthetic results than the cap confirms only the top-K candidates
  appear in the output.
- [x] 1.3 Verify self-containedness: no external asset references
  (`<link>`, `<script src=`, or any `<img src=` that isn't a `data:`
  URI); verify a unit test scans the rendered output for exactly this.

## 2. match.py integration

- [x] 2.1 Add `--report-out` to `match.py` (default
  `data/results/summary.html`); call `render_report(...)` after computing
  results, on the success path only; verify an integration test with
  `--report-out` pointing at a tmp path confirms the file is created and
  contains the correct top candidate's name. Also updated the existing
  match_cli test suite to pass `--report-out` into tmp_path — without
  this, every existing test would have written a real
  `data/results/summary.html` into the actual repo directory on every
  test run (caught and fixed before it landed in a commit).
- [x] 2.2 Verify no report file is written on the no-face-detected error
  path; verify an integration test.
- [x] 2.3 Verify the report path's parent directory is created
  automatically when it doesn't already exist; verify an integration
  test with a nested, non-existent `--report-out` directory.

## 3. Verification

- [x] 3.1 Run the full scenario set from `specs/summary-report/spec.md`
  and the ADDED `face-matching-cli` requirement, plus the entire project
  test suite, and confirm all pass; verify via the test runner's summary
  output showing zero failures. 43/43 passing. Ran the real CLI
  end-to-end (calibrate.py -> match.py --report-out) and confirmed a
  well-formed report was generated with the correct embedded images,
  names, and confidence labels; this environment has no browser
  automation tool available, so full visual rendering wasn't screenshotted
  — recommend the user do a final visual open-in-browser check.
