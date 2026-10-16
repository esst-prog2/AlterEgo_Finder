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
top N candidate identities ranked by similarity to the query, most
similar first, where N defaults to 10 and can be set with the `--top`
option. Each printed candidate SHALL be attributed to the person whose
subfolder contains the matched image, and labeled with a confidence
classification (`HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, or `NO_MATCH`)
derived from two calibrated thresholds. When the dataset has fewer than N
indexed faces, all of them are printed.

#### Scenario: Correct identity ranking
- **WHEN** the dataset contains two photos of Person A and one photo of
  Person B, and the query image is a third, different photo of Person A
- **THEN** Person A is ranked above Person B in the output, with a higher
  similarity score

#### Scenario: Output capped at 10 by default
- **WHEN** the dataset has more than 10 indexed faces and `--top` is not
  passed
- **THEN** exactly 10 candidates are printed, and they are the 10 most
  similar, in descending order of similarity

#### Scenario: Top N set on the command line
- **WHEN** `--top N` is passed with N >= 1
- **THEN** at most N candidates are printed, the N most similar

#### Scenario: Invalid top N
- **WHEN** `--top` is passed a value below 1
- **THEN** the CLI exits with a non-zero status and an error message, and
  does not run the match

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
The system SHALL use the low and high confidence thresholds from the
`config.json` file in the parent directory of the dataset directory (for
`data/celebrities/`, `data/config.json`) when that file is present, or
from the file given by `--config`, and SHALL allow both thresholds to be
overridden via CLI options.

#### Scenario: Thresholds loaded from config file
- **WHEN** a `config.json` containing threshold values exists in the
  dataset directory's parent directory, and `--config` is not passed
- **THEN** the CLI uses those values as the default low and high
  thresholds

#### Scenario: Config file given explicitly
- **WHEN** `--config <path>` is passed
- **THEN** the CLI reads the thresholds from that file instead

#### Scenario: CLI override takes precedence
- **WHEN** `--threshold-low` or `--threshold-high` is passed on the
  command line
- **THEN** that value overrides the corresponding value from the config
  file

### Requirement: Visual report generation
Given a successful match (a query image with a detectable face), the CLI
SHALL write a self-contained HTML report to a configurable output path.

#### Scenario: Report written after successful match
- **WHEN** `match.py` completes a match against a query image with a
  detectable face
- **THEN** a self-contained HTML report is written to the report output
  path (default `data/results/summary.html`)

#### Scenario: No report on no-face-detected error
- **WHEN** the query image has no detectable face
- **THEN** no report file is written

#### Scenario: Report path configurable
- **WHEN** `--report-out` is passed on the command line
- **THEN** the report is written to that path instead of the default
