## Purpose

Derives the two confidence-classification thresholds (a low, no-match
boundary and a high, high-confidence boundary) from a held-out calibration
dataset, and persists them for the matching CLI to use.

## ADDED Requirements

### Requirement: Threshold derivation from held-out data
The system SHALL compute similarity scores for same-person (intra-class)
and different-person (inter-class) pairs drawn only from a specified
calibration directory, and SHALL derive two thresholds from those scores:
a low threshold at the equal-error-rate (EER) point, and a high threshold
at a low false-accept-rate operating point on the inter-class distribution.

#### Scenario: Low threshold is the EER point
- **WHEN** calibration runs against a directory with both same-person and
  different-person pairs
- **THEN** the low threshold equals the similarity score where the
  intra-class false-reject rate equals the inter-class false-accept rate

#### Scenario: High threshold is at least as strict as the low threshold
- **WHEN** calibration computes both thresholds for the same directory
- **THEN** the high threshold is greater than or equal to the low
  threshold

### Requirement: Threshold persistence
The system SHALL write the computed low and high thresholds to
`data/config.json`.

#### Scenario: Config file written after calibration
- **WHEN** calibration completes successfully
- **THEN** `data/config.json` exists and contains both a low and a high
  threshold value
