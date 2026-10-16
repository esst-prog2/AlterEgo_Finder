## MODIFIED Requirements

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
