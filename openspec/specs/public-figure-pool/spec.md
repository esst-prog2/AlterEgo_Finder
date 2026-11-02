# public-figure-pool Specification

## Purpose
An optional candidate dataset of well-known adults, built once from Wikidata and
Wikimedia Commons with each photo's licence recorded, so a lookalike match can be
someone the viewer recognises. Matching against it stays local and offline.

## Requirements

### Requirement: Committed selection of people
The people in the pool SHALL come from a list committed to the repository,
holding identifiers, names and image file names but no images. Building the pool
SHALL NOT run a live search for people. The list SHALL contain only adults with
an English name, selected across several occupations by fame or added by hand, and SHALL NOT contain
politicians or people left out by hand.

#### Scenario: Build uses the list
- **WHEN** the pool is built
- **THEN** only people on the committed list are fetched, and no people query is
  sent to Wikidata

#### Scenario: Adults only
- **WHEN** the committed list is read
- **THEN** every listed person was at least 18 years old when the list was made

#### Scenario: No politicians
- **WHEN** a person is tagged on Wikidata as a politician, statesperson, monarch or
  revolutionary, even alongside another occupation
- **THEN** that person is not on the list

#### Scenario: Person taken off the list
- **WHEN** the pool is built after someone has been removed from the list
- **THEN** that person's image and credit leave the pool, and nothing else in the
  folder is touched

#### Scenario: Added by hand
- **WHEN** a person is on the list of hand-picked additions
- **THEN** they are on the list ahead of the others, and their image still has to pass
  the licence, author and face checks

#### Scenario: Left out by hand
- **WHEN** a person is on the list of exclusions
- **THEN** they are not on the list, whatever their occupation or fame

#### Scenario: Refreshing the list
- **WHEN** a maintainer runs the refresh command
- **THEN** the list is regenerated deterministically from Wikidata's answer, and a
  failed query leaves the existing list unchanged

### Requirement: Query photo stays out of the build
Building the pool SHALL NOT depend on or transmit any query photo, and matching
against a built pool SHALL use no network.

#### Scenario: Matching offline
- **WHEN** a photo is matched against a built pool with no network access
- **THEN** the results are shown as usual

#### Scenario: Nothing is sent
- **WHEN** the pool is built
- **THEN** its requests contain only names of Wikimedia files, never a user photo

### Requirement: Considerate, resumable build
The optional build command SHALL identify itself to Wikimedia, wait between image
requests, and honour rate-limit responses. Interrupting it SHALL lose no finished
work, and running it again SHALL continue where it stopped.

#### Scenario: Rate limited
- **WHEN** Wikimedia answers with HTTP 429
- **THEN** the command waits as told and retries, and if limited again it stops with
  a non-zero status and a message saying how to resume, keeping what it has

#### Scenario: Resume
- **WHEN** the command runs after an interruption
- **THEN** it does not fetch images it already has, and it finishes the pool

#### Scenario: Size limit
- **WHEN** a pool size is given
- **THEN** the command stops once that many usable images are saved

### Requirement: Only usable, licensed images
An image SHALL enter the pool only if it comes over HTTPS from Wikimedia's image
host, is within a size limit, decodes as an image, contains a detectable face, and
has a recorded author and a licence on the allowed list. Skipped images SHALL be
counted in the command's output.

#### Scenario: Unknown licence
- **WHEN** an image's licence is missing or not on the allowed list
- **THEN** it is skipped and the next listed person is used

#### Scenario: No face
- **WHEN** no face is detected in an image
- **THEN** it is skipped and the next listed person is used

#### Scenario: Unexpected host
- **WHEN** an image URL is not on Wikimedia's image host over HTTPS
- **THEN** it is not fetched

### Requirement: Attribution recorded with the pool
For every image in the pool, the build SHALL record the author as plain text, the
licence, and the source page, stored with the dataset.

#### Scenario: Every image attributed
- **WHEN** the build finishes
- **THEN** every image under the pool has an attribution entry, with HTML removed
  from the author

### Requirement: Thresholds of the pool's own
The build SHALL calibrate the pool's thresholds for its own size and store them
inside the pool's folder, leaving the thresholds of other datasets unchanged.

#### Scenario: Pool appears ready to use
- **WHEN** the build finishes
- **THEN** the pool is listed in the web UI's dropdown with its own calibrated
  thresholds, indexed

#### Scenario: Other datasets keep theirs
- **WHEN** the pool is built
- **THEN** `data/config.json` and the existing datasets are unchanged
