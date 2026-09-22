# summary-report Specification

## Purpose

Renders a self-contained HTML report — the query image, the top-ranked
candidates, and each candidate's confidence status — from a query image
and a set of ranked match results.

## Requirements

### Requirement: Self-contained HTML rendering
The system SHALL render a single HTML file with no external asset
references, given a query image and a set of ranked match results,
embedding all images inline.

#### Scenario: Report includes query and candidate images
- **WHEN** rendering a report for a query image and a non-empty set of
  ranked results
- **THEN** the output HTML contains the query image and each included
  candidate's image embedded inline, not referenced as a separate file

#### Scenario: Report is openable without external files
- **WHEN** the rendered HTML file is opened directly from disk
- **THEN** it displays correctly without requiring any other file to be
  present alongside it

### Requirement: Confidence status displayed per candidate
The system SHALL display each included candidate's confidence
classification (`HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, or `NO_MATCH`) in the
rendered report.

#### Scenario: Top match confidence is visible
- **WHEN** a report is rendered for results including a `HIGH_CONFIDENCE`
  top candidate
- **THEN** the rendered report visibly indicates that candidate's
  `HIGH_CONFIDENCE` status

### Requirement: Candidate list capped
The system SHALL include at most a fixed number of top-ranked candidates
in the report, even when more results are available.

#### Scenario: More results than the cap
- **WHEN** the ranked results contain more candidates than the report's
  cap
- **THEN** only the top-ranked candidates up to the cap are included in
  the report
