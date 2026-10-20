# web-ui Specification

## Purpose
A local browser page over the same matching pipeline as the CLI: the user
drops a query photo, picks a dataset, and sees the top-ranked candidates with
scores and calibrated confidence labels, without the photo leaving the machine.

## Requirements

### Requirement: Local-only serving
The web UI SHALL accept connections only from the machine it runs on
(localhost), and SHALL NOT send the uploaded photo, match results or usage
statistics to any other host.

#### Scenario: Page reachable on localhost
- **WHEN** the web UI is started from the repository root with its shipped
  configuration
- **THEN** the page is served at a `localhost` address

#### Scenario: Not reachable from the network
- **WHEN** another device on the same network requests the page at this
  machine's network address
- **THEN** the connection is refused

#### Scenario: No usage statistics
- **WHEN** the web UI runs with its shipped configuration
- **THEN** its usage-statistics collection is turned off

### Requirement: Query photo upload
The web UI SHALL accept one JPEG or PNG query photo by drag-and-drop or file
picker, and SHALL keep using that photo for later matches until it is
replaced or removed.

#### Scenario: Photo uploaded
- **WHEN** a JPEG or PNG photo with a detectable face is uploaded
- **THEN** the page shows the match results for that photo against the
  selected dataset

#### Scenario: Unreadable file
- **WHEN** an uploaded file cannot be decoded as an image
- **THEN** the page shows an error saying the image could not be read, and
  shows no candidates and no report

### Requirement: Dataset selection
The web UI SHALL offer a dropdown of the folders directly under `data/` that
already have an embedding index, and SHALL match against the selected one.
Changing the selection SHALL re-run the match on the photo already uploaded.

#### Scenario: Only indexed datasets listed
- **WHEN** `data/` holds folders with an embedding index and folders without
  one
- **THEN** the dropdown lists only the folders with an index

#### Scenario: Dataset switched without re-upload
- **WHEN** a photo is uploaded and the user selects a different dataset
- **THEN** the page shows the results of that same photo against the newly
  selected dataset, without a new upload

#### Scenario: No indexed dataset
- **WHEN** no folder under `data/` has an embedding index
- **THEN** the page tells the user to index a dataset first with the CLI,
  and offers no upload

### Requirement: Threshold control
The web UI SHALL let the user set the low and high thresholds with a single
range control that cannot place the low threshold above the high one,
preset to the calibrated thresholds of the selected dataset, and SHALL show
a notice while either value differs from the calibrated one.

#### Scenario: Preset to calibrated values
- **WHEN** a dataset whose calibrated thresholds are available is selected
- **THEN** the range control starts at those low and high values, and no
  override notice is shown

#### Scenario: Thresholds overridden
- **WHEN** the user moves either end of the range control away from the
  calibrated value
- **THEN** the candidates are relabeled with the new thresholds without
  re-uploading, and a notice says the thresholds are not the calibrated ones

#### Scenario: No calibrated thresholds
- **WHEN** the selected dataset has no calibrated thresholds available
- **THEN** the page shows an error telling the user to run the calibration
  step, and shows no candidates

### Requirement: Result cards
For a query photo with a detectable face, the web UI SHALL show the face crop
used for matching and the top N candidates, most similar first, each as a
card with the person's name, the matched image, the similarity score and the
confidence label. N SHALL default to 10 and be adjustable from 1 to 20.

#### Scenario: Top 10 by default
- **WHEN** the selected dataset has more than 10 indexed faces and the
  candidate count is not changed
- **THEN** exactly 10 cards are shown, the 10 most similar, in descending
  order of similarity

#### Scenario: Labels match the CLI
- **WHEN** the same photo, dataset and thresholds are used in the web UI and
  in the CLI
- **THEN** the cards show the same candidates, scores and labels, in the
  same order, as the CLI's output

#### Scenario: Face crop shown
- **WHEN** a photo with a detectable face is matched
- **THEN** the page shows the aligned face crop the scores were computed
  from, next to the uploaded photo

### Requirement: No-face error
If the uploaded photo contains no detectable face, the web UI SHALL show the
error "No face detected" and SHALL show no candidates and offer no report.

#### Scenario: Photo without a face
- **WHEN** a readable image with no detectable face is uploaded
- **THEN** the page shows "No face detected", no cards, and no report preview
  or download

### Requirement: Report preview and download
For a query photo with a detectable face, the web UI SHALL produce the same
self-contained HTML report as the CLI for the current results, show it on the
page, and offer it as a file download.

#### Scenario: Report offered after a match
- **WHEN** a photo with a detectable face has been matched
- **THEN** the page offers a download of a self-contained HTML report with
  the query image and the top candidates with their labels, and previews it

#### Scenario: Report follows the thresholds
- **WHEN** the user changes the thresholds after a match
- **THEN** the report offered for download shows the labels under the new
  thresholds

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
