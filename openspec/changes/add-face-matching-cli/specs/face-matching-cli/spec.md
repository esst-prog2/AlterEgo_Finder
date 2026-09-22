## Purpose

A command-line tool that, given a query face image and a dataset directory
of labeled face images, indexes the dataset once and reports the dataset's
identities ranked by similarity to the query.

## ADDED Requirements

### Requirement: Dataset auto-indexing and caching
The system SHALL build an embedding index from the images under a dataset
directory the first time that directory is used, and SHALL cache the index
for reuse by later runs against the same directory.

#### Scenario: Cache reused if fresh
- **WHEN** the CLI is run against a dataset directory whose cached index
  already exists and is up to date with the directory's contents
- **THEN** the system reuses the cached index without recomputing it

#### Scenario: Cache rebuilt if stale
- **WHEN** the dataset directory's contents change after a cached index was
  built
- **THEN** the next run against that directory rebuilds the index rather
  than matching against the stale cache

### Requirement: Ranked match output
Given a query image and a dataset directory, the system SHALL print the
dataset's candidate identities ranked by similarity to the query, most
similar first, with each candidate attributed to the person whose
subfolder contains the matched image.

#### Scenario: Correct identity ranking
- **WHEN** the dataset contains two photos of Person A and one photo of
  Person B, and the query image is a third, different photo of Person A
- **THEN** Person A is ranked above Person B in the output, with a higher
  similarity score

### Requirement: No-face-detected error handling
If the query image contains no detectable face, the CLI SHALL exit with
status code 1 and print the message `Error: No face detected in input
image`.

#### Scenario: Query image has no face
- **WHEN** the CLI is run with a query image containing no detectable face
- **THEN** the process exits with status code 1 and prints
  `Error: No face detected in input image`
