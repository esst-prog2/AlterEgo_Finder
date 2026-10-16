## MODIFIED Requirements

### Requirement: Threshold persistence
The system SHALL write the computed low and high thresholds to the
`config.json` file in the parent directory of the calibration directory
(for `data/calibration/`, `data/config.json`), or to the path given by
`--config-out`.

#### Scenario: Config file written after calibration
- **WHEN** calibration completes successfully and `--config-out` is not
  passed
- **THEN** `config.json` exists in the calibration directory's parent
  directory and contains both a low and a high threshold value

#### Scenario: Config output path given explicitly
- **WHEN** calibration completes successfully with `--config-out <path>`
- **THEN** the thresholds are written to that path
