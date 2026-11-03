## ADDED Requirements

### Requirement: Works from any install folder
The program SHALL work the same when the repository, a dataset or a query photo is in a
folder whose path has non-ASCII characters. This SHALL NOT change any result: for the same
files, scores and thresholds SHALL be identical to those from an ASCII path.

#### Scenario: Repository in an accented folder
- **WHEN** the repository is in a folder such as `C:\Users\György\Project`
- **THEN** both models load, and the CLI and the web page match a photo as usual

#### Scenario: Dataset and query photo in accented folders
- **WHEN** a dataset folder, a person's folder or a query photo's path has non-ASCII characters
- **THEN** the images are read, indexed and matched, with none silently dropped

#### Scenario: Same results as an ASCII path
- **WHEN** the same files are matched from an accented folder and from an ASCII folder
- **THEN** the scores and thresholds are identical

#### Scenario: Missing or unreadable image
- **WHEN** an image file is missing or is not a readable image
- **THEN** it is handled as before: the CLI and the page report the error, and indexing skips it
