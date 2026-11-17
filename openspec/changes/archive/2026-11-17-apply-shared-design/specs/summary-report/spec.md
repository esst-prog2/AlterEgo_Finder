## ADDED Requirements

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
