## MODIFIED Requirements

### Requirement: Ranked match output
Given a query image and a dataset directory, the system SHALL print the
dataset's candidate identities ranked by similarity to the query, most
similar first, with each candidate attributed to the person whose
subfolder contains the matched image, and each candidate labeled with a
confidence classification (`HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, or
`NO_MATCH`) derived from two calibrated thresholds.

#### Scenario: Correct identity ranking
- **WHEN** the dataset contains two photos of Person A and one photo of
  Person B, and the query image is a third, different photo of Person A
- **THEN** Person A is ranked above Person B in the output, with a higher
  similarity score

#### Scenario: High-confidence classification
- **WHEN** a candidate's similarity score is at or above the high
  threshold
- **THEN** that candidate is labeled `HIGH_CONFIDENCE`

#### Scenario: Low-confidence classification
- **WHEN** a candidate's similarity score is at or above the low
  threshold but below the high threshold
- **THEN** that candidate is labeled `LOW_CONFIDENCE`

#### Scenario: No-match classification
- **WHEN** a candidate's similarity score is below the low threshold
- **THEN** that candidate is labeled `NO_MATCH`

## ADDED Requirements

### Requirement: Threshold configuration
The system SHALL use the low and high confidence thresholds from
`data/config.json` when that file is present, and SHALL allow both to be
overridden via CLI options.

#### Scenario: Thresholds loaded from config file
- **WHEN** `data/config.json` exists and contains threshold values
- **THEN** the CLI uses those values as the default low and high
  thresholds

#### Scenario: CLI override takes precedence
- **WHEN** `--threshold-low` or `--threshold-high` is passed on the
  command line
- **THEN** that value overrides the corresponding value from
  `data/config.json`
