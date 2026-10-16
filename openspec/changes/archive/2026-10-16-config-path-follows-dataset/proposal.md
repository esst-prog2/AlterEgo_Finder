## Why

The face-matching-cli and threshold-calibration specs say thresholds are
read from and written to `data/config.json`. The code uses the
`config.json` in the parent directory of `--dataset` (match.py) and of
`--calibration-dir` (calibrate.py). Under the README's `data/` layout
that's the same file, but for a dataset kept anywhere else the spec
describes the wrong file. Found by the HW6 docs/spec review.

## What Changes

- Reword both requirements to name the file the code actually uses, with
  `data/config.json` as the example for the standard layout.
- No code change: the specs are brought in line with existing behaviour,
  which keeps a dataset's thresholds beside that dataset.
- Add tests for the two default-path scenarios, which nothing covers today.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `face-matching-cli`: "Threshold configuration" reads the default config
  from `--dataset`'s parent directory, not a fixed `data/config.json`.
- `threshold-calibration`: "Threshold persistence" writes to
  `--calibration-dir`'s parent directory by default, or `--config-out`.

## Impact

- `openspec/specs/face-matching-cli/spec.md`,
  `openspec/specs/threshold-calibration/spec.md` (on archive).
- Tests: two new CLI tests; match.py and calibrate.py unchanged.
