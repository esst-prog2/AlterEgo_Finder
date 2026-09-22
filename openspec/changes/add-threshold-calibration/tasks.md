## 1. Setup

- [x] 1.1 Create `face_pipeline/calibration.py` and `calibrate.py` module
  stubs; verify both import cleanly.
- [x] 1.2 Build an LFW-style calibration fixture dataset under
  `tests/fixtures/calibration/` — disjoint identities from
  `tests/fixtures/dataset/`, with at least 2 people having 2+ photos each
  (for intra-class pairs) and at least one more identity (for inter-class
  pairs); verify the directory structure and photo counts.

## 2. Pair sampling and threshold computation

- [x] 2.1 Implement intra-/inter-class pair sampling in
  `face_pipeline/calibration.py`, capping the number of inter-class pairs;
  verify a unit test on the fixture calibration set produces the expected
  intra-class pair count and a bounded inter-class pair count.
- [x] 2.2 Implement pairwise similarity scoring (reusing
  `extract_embedding`) producing intra-class and inter-class score lists;
  verify a unit test checks all scores fall in `[-1, 1]` and that
  intra-class scores are, on average, higher than inter-class scores on
  the fixture set.
- [x] 2.3 Implement EER computation for the low threshold; verify a unit
  test against a hand-constructed pair of score distributions with a known
  EER point (low-threshold-is-EER-point scenario).
- [x] 2.4 Implement the 1%-false-accept-rate search for the high
  threshold; verify a unit test against a hand-constructed inter-class
  distribution with a known 1%-FAR score, and a unit test confirming
  `high >= low` on the fixture calibration set (high-threshold-at-least-
  as-strict scenario).

## 3. calibrate.py CLI and config output

- [x] 3.1 Implement the `calibrate.py` CLI (`--calibration-dir`, default
  `data/calibration/`) wiring pair sampling and threshold computation;
  verify an integration test running `calibrate.py` against the fixture
  calibration dataset exits 0.
- [x] 3.2 Write `data/config.json` (`threshold_low`, `threshold_high`)
  after calibration; verify an integration test confirms the file exists
  and contains both keys as numbers after running `calibrate.py` against
  the fixture set (config-file-written-after-calibration scenario).

## 4. match.py confidence classification

- [x] 4.1 Add `--threshold-low`/`--threshold-high` options to `match.py`,
  defaulting from `data/config.json` when present; verify
  `python match.py --help` documents both flags, and an integration test
  confirms a CLI-passed value overrides the config file value (CLI-
  override-takes-precedence scenario).
- [x] 4.2 Implement the error path when neither `data/config.json` nor
  both CLI threshold flags are available; verify an integration test
  running `match.py` with no config file and no threshold flags exits
  non-zero with a clear message.
- [x] 4.3 Implement per-candidate classification
  (`HIGH_CONFIDENCE`/`LOW_CONFIDENCE`/`NO_MATCH`) and add the label to
  each ranked output line; verify integration tests covering all three
  classification scenarios using fixed thresholds against known fixture
  scores.
- [x] 4.4 Confirm the existing correct-identity-ranking behavior from
  `add-face-matching-cli` still holds with the new output format (ranking
  order unaffected by the added label); verify by updating the existing
  ranking integration test to parse the new line format.

## 5. Verification

- [x] 5.1 Run the full scenario set from `specs/threshold-calibration/spec.md`
  and the modified `face-matching-cli` requirements as automated tests and
  confirm all pass; verify via the test runner's summary output showing
  zero failures.
