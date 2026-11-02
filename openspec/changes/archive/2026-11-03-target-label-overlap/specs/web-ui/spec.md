## MODIFIED Requirements

### Requirement: Similarity target
For a query photo with a detectable face, the web UI SHALL show a similarity
target: the query at the centre and every indexed face at a distance from the
centre of exactly one minus its similarity score, with two rings at the
current low and high thresholds. Direction from the centre SHALL carry no
meaning, and the page SHALL say so. The top N candidates SHALL be named;
other faces SHALL be shown unlabeled. Names SHALL stay readable: with the default
10 names, no name SHALL overlap another name, another named face, the ring legend
or the chart's edge. Avoiding an overlap SHALL move only the name, never a face.

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

#### Scenario: Self-match much closer than the next face
- **WHEN** the #1 face is much closer to the centre than the #2 face, as in a
  self-match, with the default 10 names
- **THEN** both names can be read in full, and each face stays at its exact distance

#### Scenario: No collision to avoid
- **WHEN** a name beside its face, pointing outward, overlaps nothing
- **THEN** the name stays there

#### Scenario: More names than fit
- **WHEN** the candidate count is so high that a name has no free place
- **THEN** the name goes where it overlaps least, and every name is still drawn

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
