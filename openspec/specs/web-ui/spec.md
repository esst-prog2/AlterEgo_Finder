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
Each entry SHALL show a readable name that keeps the folder name visible
(for example "Public figures (wikidata)"). The public datasets SHALL come
first (the pool, then LFW), followed by any other folders in name order,
shown with their exact folder names. When the public-figure pool
(`wikidata`) is indexed it SHALL be selected when the page opens; otherwise
the first folder in that order. Changing the selection SHALL re-run the
match on the photo already uploaded.

#### Scenario: Only indexed datasets listed
- **WHEN** `data/` holds folders with an embedding index and folders without
  one
- **THEN** the dropdown lists only the folders with an index

#### Scenario: Readable names
- **WHEN** the dropdown lists `wikidata`, `celebrities` and a folder of the
  user's own
- **THEN** they read "Public figures (wikidata)", "LFW faces (celebrities)"
  and the user's folder name

#### Scenario: Pool selected by default
- **WHEN** the page opens and `wikidata` is among the indexed folders
- **THEN** `wikidata` is the selected dataset

#### Scenario: Dataset switched without re-upload
- **WHEN** a photo is uploaded and the user selects a different dataset
- **THEN** the page shows the results of that same photo against the newly
  selected dataset, without a new upload

#### Scenario: No indexed dataset
- **WHEN** no folder under `data/` has an embedding index
- **THEN** the page tells the user to run the setup command, or to index a
  dataset of their own with the CLI, and offers no upload

#### Scenario: Public datasets first
- **WHEN** the dropdown lists `celebrities`, `wikidata`, `celebrities_plus_me`
  and `wikidata_plus_me`
- **THEN** the order is "Public figures (wikidata)", "LFW faces
  (celebrities)", `celebrities_plus_me`, `wikidata_plus_me`

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
If the uploaded photo contains no detectable face, the web UI SHALL show an
error that starts with "No face detected", says what usually causes it and
what to try, and SHALL show no candidates and offer no report.

#### Scenario: Photo without a face
- **WHEN** a readable image with no detectable face is uploaded
- **THEN** the page shows "No face detected" with a suggestion to try a
  photo where one face looks at the camera and fills a good part of the
  frame, no cards, and no report preview or download

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

### Requirement: Shared look and logo
The page SHALL follow the project's shared design system (DESIGN.md): a
paper-coloured background ruled with its printed grid, navy as the only
accent colour (information notices included), square corners, 2 px navy
frames around the upload area and each result card, the shared text font,
headings and card names in the shared display font in capitals, scores set
as ink figures in the display font, and the shared label colours, so that a
card's label, the target's dots, the promo page and the tour video use the
same green for Same person, gold for Alter Ego and grey for Not You. The
page SHALL show the AlterEgo Finder logo (the target in miniature beside
the name) at the top of its sidebar and as the browser-tab icon. Fonts and
the logo SHALL be served by the page itself from the user's machine; the
page SHALL NOT load fonts, images or styles from the network.

#### Scenario: Logo on the page
- **WHEN** the page is opened
- **THEN** the AlterEgo Finder logo appears at the top of the sidebar and
  as the browser tab's icon

#### Scenario: Shared label colours
- **WHEN** a match is shown
- **THEN** each card's label uses green #1a7f37 for Same person, gold
  #d4a72c for Alter Ego and grey #8c959f for Not You, the same colours as
  the target's dots for those labels

#### Scenario: Shared fonts and colours
- **WHEN** the page is opened
- **THEN** its background is the shared paper colour with its grid, its
  accent the shared navy, its text set in the shared body font and its
  headings in the shared display font in capitals

#### Scenario: Cards framed, scores as figures
- **WHEN** a match is shown
- **THEN** each result card is framed by a 2 px navy rule, and its score is
  set in ink in the display font, not as green code

#### Scenario: Nothing loaded from the network
- **WHEN** the page is opened and a match is shown
- **THEN** every font, image and stylesheet it loads comes from the local
  server on localhost or is inline, and no request goes to another host

### Requirement: Verdict line
For a query photo with a detectable face, the web UI SHALL state the result
in one sentence directly below the upload control, before the photo, the
target and the cards. The sentence SHALL name the outcome with the plain
label: when the top candidate is labelled Same person, its name, score and
"Same person"; when no candidate reaches Same person but one reaches Alter
Ego, that nobody in the dataset is the same person, then the closest Alter
Ego's name and score; when every candidate is Not You, that nobody in the
dataset is close. Names SHALL be shown as readable person names (see
"Readable person names"), as text, never as markup.

#### Scenario: A same-person match
- **WHEN** the top candidate is labelled `HIGH_CONFIDENCE`
- **THEN** the verdict line names that person with its score to four
  decimals and the label "Same person"

#### Scenario: Only lookalikes
- **WHEN** no candidate is labelled `HIGH_CONFIDENCE` and the top candidate
  is labelled `LOW_CONFIDENCE`
- **THEN** the verdict line says nobody in the dataset is the same person
  and names the closest Alter Ego with its score

#### Scenario: Nobody close
- **WHEN** every candidate is labelled `NO_MATCH`
- **THEN** the verdict line says nobody in the dataset is close, with the
  label "Not You"

#### Scenario: Markup in a name
- **WHEN** the top candidate's folder name contains HTML or Markdown
- **THEN** the verdict line shows it as literal text

### Requirement: Readable on any screen
The web UI SHALL keep every caption, note and upload hint at a contrast of
at least 4.5:1 against its background, SHALL fit the similarity target within the
width of a 390 px screen without cutting off rings or names, SHALL give
the target a text description of what it shows and each card photo a text
alternative naming the person, SHALL order its headings without skipping a
level, SHALL NOT show Streamlit's deploy toolbar, and SHALL present the report
download as the page's primary (navy) button.

#### Scenario: Phone width
- **WHEN** a match is shown in a 390 px wide window
- **THEN** the whole target, both rings and every named face are within the
  window, and the page does not scroll sideways

#### Scenario: Screen reader
- **WHEN** a match is shown
- **THEN** the target has a text description stating how many shown faces
  fall in each label, and every card photo has a text alternative with the
  person's name

#### Scenario: Caption contrast
- **WHEN** the page is opened and a match is shown
- **THEN** every caption measures at least 4.5:1 against the page's paper

#### Scenario: Upload hint contrast
- **WHEN** the page is opened, and when a photo has been uploaded
- **THEN** the upload hint and the uploaded file's size measure at least
  4.5:1 against their background

#### Scenario: Download as the primary action
- **WHEN** a match is shown
- **THEN** the report download is a navy primary button

### Requirement: Calibrated thresholds only
The web UI SHALL label every candidate with the selected dataset's
calibrated thresholds and SHALL offer no control to change them.

#### Scenario: No threshold control
- **WHEN** the page is opened with a calibrated dataset
- **THEN** it shows no slider or input for the thresholds, and the labels
  equal the CLI's with the same dataset and its calibrated thresholds

#### Scenario: No calibrated thresholds
- **WHEN** the selected dataset has no calibrated thresholds available
- **THEN** the page shows an error telling the user to run the calibration
  step, and shows no candidates

### Requirement: Report for the selected dataset
For a query photo with a detectable face, the web UI SHALL produce the same
self-contained HTML report as the CLI for the current results, show it on the
page, and offer it as a file download.

#### Scenario: Report offered after a match
- **WHEN** a photo with a detectable face has been matched
- **THEN** the page offers a download of a self-contained HTML report with
  the query image and the top candidates with their labels, and previews it

#### Scenario: Report follows the dataset
- **WHEN** the user switches the dataset after a match
- **THEN** the report offered for download shows the candidates and labels
  for the newly selected dataset

### Requirement: Similarity target at calibrated thresholds
For a query photo with a detectable face, the web UI SHALL show a similarity
target: the query at the centre and every indexed face at a distance from the
centre of exactly one minus its similarity score, with two rings at the
selected dataset's calibrated low and high thresholds. Direction from the
centre SHALL carry no meaning, and the page SHALL say so. The top N
candidates SHALL be named; other faces SHALL be shown unlabeled. Names SHALL
stay readable: with the default 10 names, no name SHALL overlap another name,
another named face, the ring legend or the chart's edge. Avoiding an overlap
SHALL move only the name, never a face.

#### Scenario: Distances are exact
- **WHEN** a photo with a detectable face is matched against a dataset
- **THEN** each indexed face is plotted at a distance from the centre equal to
  one minus its similarity score, for every indexed face

#### Scenario: Rings at the calibrated thresholds
- **WHEN** a photo is matched against a dataset
- **THEN** the rings are drawn at distances of one minus that dataset's
  calibrated low and high thresholds, so the faces inside the inner ring are
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

### Requirement: Readable person names
The web UI SHALL show each person's name with the underscores of its
dataset folder name replaced by spaces ("Leonardo_DiCaprio" as "Leonardo
DiCaprio") in the verdict line, on the cards, in the similarity target's
names and details, and in the card photos' text alternatives. Names SHALL
stay text, never markup. The candidates, their order, scores and labels
SHALL stay those of the CLI, which keeps the folder names.

#### Scenario: Underscores become spaces
- **WHEN** the top candidate's folder is `Leonardo_DiCaprio`
- **THEN** the verdict, its card, the target and the photo's text
  alternative say "Leonardo DiCaprio"

#### Scenario: Same candidates as the CLI
- **WHEN** the same photo and dataset are used in the web UI and in the CLI
- **THEN** the cards show the same candidates in the same order with the
  same scores and labels, each name being the CLI's with spaces for
  underscores
