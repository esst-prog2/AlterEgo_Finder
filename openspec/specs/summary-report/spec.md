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
classification in the rendered report as its plain name followed by the
technical label in parentheses: "Same person (HIGH_CONFIDENCE)", "Alter
Ego (LOW_CONFIDENCE)" or "Not You (NO_MATCH)", so a reader sees the plain
name and a developer still finds the CLI's label.

#### Scenario: Top match confidence is visible
- **WHEN** a report is rendered for results including a `HIGH_CONFIDENCE`
  top candidate
- **THEN** the rendered report visibly indicates that candidate's
  `HIGH_CONFIDENCE` status

#### Scenario: Plain name with the technical label
- **WHEN** a report is rendered for candidates of all three classifications
- **THEN** each shows "Same person (HIGH_CONFIDENCE)", "Alter Ego
  (LOW_CONFIDENCE)" or "Not You (NO_MATCH)"

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

### Requirement: Shared look and logo in the report
The report SHALL follow the project's shared design system (DESIGN.md):
paper background, navy rules framing the query and each candidate, square
corners, the shared fonts, and each candidate's confidence classification
shown beside a dot in its shared label colour (green #1a7f37 for
`HIGH_CONFIDENCE`, gold #d4a72c for `LOW_CONFIDENCE`, grey #8c959f for
`NO_MATCH`). The report SHALL show the AlterEgo Finder logo in its header.
The fonts and the logo SHALL be embedded in the file, so the report stays
self-contained.

#### Scenario: Logo in the header
- **WHEN** a report is rendered
- **THEN** its header shows the AlterEgo Finder logo, embedded inline

#### Scenario: Label colours by classification
- **WHEN** a report is rendered for candidates of all three classifications
- **THEN** each candidate's classification is shown with a dot in green,
  gold or grey matching `HIGH_CONFIDENCE`, `LOW_CONFIDENCE` and `NO_MATCH`

#### Scenario: Still self-contained
- **WHEN** the rendered report is opened directly from disk with no
  network connection
- **THEN** it shows its fonts, logo and images without any other file,
  and contains no reference to an external URL other than the photo
  credits' source links
