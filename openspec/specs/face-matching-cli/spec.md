# face-matching-cli Specification

## Purpose

A command-line tool that, given a query face image and a dataset directory
of labeled face images, indexes the dataset once and reports the dataset's
identities ranked by similarity to the query.

## Requirements

### Requirement: Dataset auto-indexing and caching
The system SHALL build an embedding index from the images under a dataset
directory the first time that directory is used, and SHALL cache the index
for reuse by later runs against the same directory.

#### Scenario: Cache reused if fresh
- **WHEN** the CLI is run against a dataset directory whose cached index
  already exists and is up to date with the directory's contents
- **THEN** the system reuses the cached index without recomputing it

#### Scenario: Cache rebuilt if stale
- **WHEN** the dataset directory's contents change after a cached index was
  built
- **THEN** the next run against that directory rebuilds the index rather
  than matching against the stale cache

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

### Requirement: No-face-detected error handling
If the query image contains no detectable face, the CLI SHALL exit with
status code 1 and print the message `Error: No face detected in input
image`.

#### Scenario: Query image has no face
- **WHEN** the CLI is run with a query image containing no detectable face
- **THEN** the process exits with status code 1 and prints
  `Error: No face detected in input image`

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
