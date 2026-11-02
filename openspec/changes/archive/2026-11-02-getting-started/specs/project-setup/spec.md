## Purpose

Takes a fresh clone of the repository to a working program with one command:
it obtains the public face dataset, builds the same dataset for everyone, and
calibrates the thresholds, without storing any images in the repository.

## ADDED Requirements

### Requirement: One-command setup
A single setup command run from the repository root SHALL leave the project
ready to match: the candidate dataset and calibration dataset built, calibrated
thresholds written to `data/config.json`, and the candidate dataset indexed.

#### Scenario: Fresh clone
- **WHEN** the setup command runs in a fresh clone with network access
- **THEN** it exits with status 0, and `data/celebrities/`,
  `data/calibration/`, `data/config.json` and the candidate dataset's index exist

#### Scenario: Web UI works after setup
- **WHEN** setup has finished and the web UI is started
- **THEN** `celebrities` is listed in the dataset dropdown with calibrated
  thresholds, and an uploaded photo with a face gets result cards

### Requirement: Verified download
The setup command SHALL verify the downloaded dataset archive against a fixed
SHA-256 checksum before using it, and SHALL NOT use an archive that fails. An
interrupted download SHALL NOT leave a file that a later run treats as complete.

#### Scenario: Checksum mismatch
- **WHEN** the archive's checksum differs from the expected one
- **THEN** the command exits with a non-zero status and an error message, and
  builds no dataset from it

#### Scenario: Download fails
- **WHEN** the download fails or stalls
- **THEN** the command exits with a non-zero status and an error message saying
  how to retry, and no partial file remains under the archive's final name

#### Scenario: Archive already present
- **WHEN** a valid archive already exists, or one is given on the command line
- **THEN** it is used without downloading

### Requirement: Reproducible dataset
The setup command SHALL build the datasets from a list of exact image paths
committed to the repository, so that every run produces the same images. The
repository SHALL contain the list, not the images.

#### Scenario: Same faces for everyone
- **WHEN** setup runs on two machines
- **THEN** both get byte-identical images in `data/celebrities/` and
  `data/calibration/`

#### Scenario: Datasets are disjoint
- **WHEN** the committed list is read
- **THEN** it names 500 candidate identities with one image each and 200
  calibration identities, with no identity in both

#### Scenario: Image missing from the archive
- **WHEN** a listed image is not in the archive
- **THEN** the command exits with a non-zero status naming the image

### Requirement: Safe to run again
Running the setup command again SHALL NOT repeat finished work or change
anything outside the files it manages. Existing thresholds SHALL be kept unless
the user asks to recalibrate.

#### Scenario: Second run
- **WHEN** setup runs again after a complete run
- **THEN** it exits with status 0 without downloading or recalibrating, and
  `data/config.json` is unchanged

#### Scenario: Interrupted first run
- **WHEN** setup runs after an earlier run stopped partway
- **THEN** it completes the missing steps and exits with status 0

#### Scenario: Other data untouched
- **WHEN** `data/` holds other folders, such as the user's own photos or
  datasets
- **THEN** setup leaves them unchanged

#### Scenario: Recalibrate on request
- **WHEN** the user passes the recalibrate option
- **THEN** the thresholds are computed again and `data/config.json` is rewritten
