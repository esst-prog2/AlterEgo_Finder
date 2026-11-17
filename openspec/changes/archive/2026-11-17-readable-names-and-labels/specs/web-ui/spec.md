## ADDED Requirements

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

## MODIFIED Requirements

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
