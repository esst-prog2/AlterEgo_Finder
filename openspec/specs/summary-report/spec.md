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

### Requirement: Photo attribution in the report
When a dataset records attribution for its images, the HTML report SHALL show
each included candidate's photo author and licence, and a link to the photo's
source page. Attribution text SHALL be treated as untrusted and shown as plain
text.

#### Scenario: Attributed candidate
- **WHEN** a report includes a candidate whose image has recorded attribution
- **THEN** the card in the report shows the author, the licence and a source link

#### Scenario: Candidate without attribution
- **WHEN** a candidate's image has no recorded attribution, as with LFW
- **THEN** the report shows the card without an attribution line

#### Scenario: Markup in an author name
- **WHEN** a recorded author name contains HTML
- **THEN** the report shows it as literal text, and no element or script from it
  is created
