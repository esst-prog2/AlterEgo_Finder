## MODIFIED Requirements

### Requirement: Threshold derivation from held-out data
The system SHALL compute similarity scores for same-person (intra-class)
and different-person (inter-class) pairs drawn only from a specified
calibration directory, and SHALL derive the low threshold at the
equal-error-rate (EER) point of those pairwise scores. The system SHALL
derive the high threshold at a low false-accept-rate operating point on the
distribution of top-1 (maximum) similarity scores obtained when querying
held-out identities that are absent from an index of the same size as the
dataset being matched against, not on the pairwise inter-class distribution.

#### Scenario: Low threshold is the EER point
- **WHEN** calibration runs against a directory with both same-person and
  different-person pairs
- **THEN** the low threshold equals the similarity score where the
  intra-class false-reject rate equals the inter-class false-accept rate

#### Scenario: High threshold bounds the absent-stranger rank-1 false-accept rate
- **WHEN** calibration runs for a dataset of N indexed faces, and queries of
  held-out identities absent from an N-face index are scored by their top-1
  similarity
- **THEN** at most the target false-accept rate (1%) of those top-1 scores
  are at or above the high threshold

#### Scenario: High threshold grows with index size
- **WHEN** calibration runs for a larger index size N
- **THEN** the high threshold is greater than or equal to the high threshold
  derived for a smaller N from the same calibration data

#### Scenario: High threshold is at least as strict as the low threshold
- **WHEN** calibration computes both thresholds for the same directory
- **THEN** the high threshold is greater than or equal to the low
  threshold
