## ADDED Requirements

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
