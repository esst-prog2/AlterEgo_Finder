## ADDED Requirements

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
