## MODIFIED Requirements

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
