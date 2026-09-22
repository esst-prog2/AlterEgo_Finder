## Purpose

Delivers the project's ONNX model weight files on demand — downloading
them if not already present locally and verifying their integrity via
SHA-256 before they are trusted for inference.

## ADDED Requirements

### Requirement: Download on first use
The system SHALL download a required model file from its known source if
it is not already present locally, before that model is used for
inference.

#### Scenario: Model file missing locally
- **WHEN** a model file required for detection or embedding is not
  present on disk
- **THEN** the system downloads it from the configured source before
  proceeding

#### Scenario: Model file already present
- **WHEN** a required model file already exists locally and passes
  checksum verification
- **THEN** the system uses it without re-downloading

### Requirement: Checksum verification before use
The system SHALL verify a model file's SHA-256 checksum against a known
expected value before using it for inference, whether the file was just
downloaded or already present locally.

#### Scenario: Checksum matches
- **WHEN** a model file's computed SHA-256 matches the expected value
- **THEN** the system proceeds to load and use it

#### Scenario: Checksum does not match
- **WHEN** a model file's computed SHA-256 does not match the expected
  value
- **THEN** the system SHALL NOT load that file for inference, and SHALL
  report a clear error identifying the mismatch

### Requirement: Clear failure on download error
If a required model file cannot be downloaded (network failure, missing
source, etc.), the system SHALL fail with a clear error rather than
proceeding without the model or silently using a different file.

#### Scenario: Download fails
- **WHEN** downloading a required model file fails
- **THEN** the system reports a clear error naming the model file and
  does not proceed to inference
