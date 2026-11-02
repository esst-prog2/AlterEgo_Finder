## MODIFIED Requirements

### Requirement: Threshold configuration
The system SHALL use the low and high confidence thresholds from a
`config.json` inside the dataset directory when that file is present,
otherwise from the `config.json` file in the parent directory of the dataset
directory (for `data/celebrities/`, `data/config.json`), or from the file given
by `--config`, and SHALL allow both thresholds to be overridden via CLI options.

#### Scenario: Thresholds loaded from config file
- **WHEN** a `config.json` containing threshold values exists in the
  dataset directory's parent directory, and `--config` is not passed
- **THEN** the CLI uses those values as the default low and high
  thresholds

#### Scenario: Dataset's own thresholds take precedence
- **WHEN** a `config.json` exists both inside the dataset directory and in its
  parent directory, and `--config` is not passed
- **THEN** the CLI uses the values from the one inside the dataset directory

#### Scenario: Config file given explicitly
- **WHEN** `--config <path>` is passed
- **THEN** the CLI reads the thresholds from that file instead

#### Scenario: CLI override takes precedence
- **WHEN** `--threshold-low` or `--threshold-high` is passed on the
  command line
- **THEN** that value overrides the corresponding value from the config
  file
