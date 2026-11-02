## ADDED Requirements

### Requirement: Photo attribution on the page
When the selected dataset records attribution for its images, each result card
and each named face's tooltip SHALL show the photo's author and licence, and the
card SHALL link to the photo's source page. Attribution text SHALL be shown as
plain text.

#### Scenario: Attributed card
- **WHEN** a result card shows an image with recorded attribution
- **THEN** the card shows the author, the licence and a source link

#### Scenario: Dataset without attribution
- **WHEN** the selected dataset records no attribution, as with LFW
- **THEN** the cards look as they do today

#### Scenario: Markup in an author name
- **WHEN** a recorded author name contains Markdown or HTML
- **THEN** the card shows it as literal text
