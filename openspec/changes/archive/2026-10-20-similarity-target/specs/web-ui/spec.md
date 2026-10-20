## ADDED Requirements

### Requirement: Similarity target
For a query photo with a detectable face, the web UI SHALL show a similarity
target: the query at the centre and every indexed face at a distance from the
centre of exactly one minus its similarity score, with two rings at the
current low and high thresholds. Direction from the centre SHALL carry no
meaning, and the page SHALL say so. The top N candidates SHALL be named;
other faces SHALL be shown unlabeled.

#### Scenario: Distances are exact
- **WHEN** a photo with a detectable face is matched against a dataset
- **THEN** each indexed face is plotted at a distance from the centre equal to
  one minus its similarity score, for every indexed face

#### Scenario: Threshold rings follow the slider
- **WHEN** the user changes the low or high threshold
- **THEN** the rings are redrawn at distances of one minus the new low and
  one minus the new high threshold, so the faces inside the inner ring are
  exactly those labeled `HIGH_CONFIDENCE`

#### Scenario: Top candidates named
- **WHEN** the candidate count is N
- **THEN** the N top-ranked faces are drawn highlighted with their rank and
  person's name, the #1 face also with its similarity score, and all other
  indexed faces are drawn without names

#### Scenario: Photos of one person side by side
- **WHEN** several of the top N faces are photos of the same person
- **THEN** those photos are placed next to each other around the centre

#### Scenario: Point details on hover
- **WHEN** the user hovers over a face on the target
- **THEN** its person's name, similarity score and confidence label are shown,
  and for one of the top N faces also a small image of the matched face

#### Scenario: No target without a match
- **WHEN** the uploaded photo has no detectable face or cannot be read
- **THEN** no similarity target is shown

### Requirement: Plain-language confidence names
The web UI SHALL show each confidence label only by its plain-language name:
"Same person" for `HIGH_CONFIDENCE`, "Alter Ego" for `LOW_CONFIDENCE` and
"Not You" for `NO_MATCH`. The technical label names SHALL NOT appear on the
page; they remain in the CLI output and the HTML report.

#### Scenario: Card shows the plain name
- **WHEN** a result card for a `LOW_CONFIDENCE` candidate is shown
- **THEN** the card shows "Alter Ego" and does not show `LOW_CONFIDENCE`

#### Scenario: Plain names match the CLI one to one
- **WHEN** the same photo, dataset and thresholds are used in the web UI and
  in the CLI
- **THEN** each card's plain name corresponds to the CLI's label for that
  candidate ("Same person" to `HIGH_CONFIDENCE`, "Alter Ego" to
  `LOW_CONFIDENCE`, "Not You" to `NO_MATCH`)

#### Scenario: Target legend uses the plain names
- **WHEN** the similarity target is shown
- **THEN** its legend explains the inner ring as "Same person", the band
  between the rings as "Alter Ego", and the area outside as "Not You",
  without the technical label names
