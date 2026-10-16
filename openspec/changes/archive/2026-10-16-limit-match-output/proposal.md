## Why

`match.py` prints every ranked candidate: 500 lines for the 500-face
`data/celebrities` index (HW5 step 6), so the matches worth reading scroll
away. README section 1 promises "the top matching records". The HW6
correctness review left this open because the face-matching-cli spec
currently requires printing all of the dataset's candidates.

## What Changes

- `match.py` prints only the top 10 ranked candidates by default, the same
  number the HTML report already shows.
- New `--top N` option sets how many candidates are printed (N >= 1); a
  value below 1 is a usage error.
- Classification, ranking order and the HTML report are unchanged.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `face-matching-cli`: "Ranked match output" prints the top N candidates
  (default 10, set by `--top`) instead of every candidate.

## Impact

- `match.py`: new `--top` argument; the print loop is limited to the top N.
- Tests: new CLI tests for the default cap and `--top`; existing CLI tests
  use a 3-image dataset, below the cap, so they're unaffected.
- README section 1 already describes this behaviour; no doc change needed
  beyond the spec.
