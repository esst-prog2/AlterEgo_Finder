## MODIFIED Requirements

### Requirement: Clear failure on download error
If a required model file cannot be downloaded (network failure, missing
source, a connection that stalls, etc.), the system SHALL fail with a clear
error rather than proceeding without the model, silently using a different
file, or waiting indefinitely.

#### Scenario: Download fails
- **WHEN** downloading a required model file fails
- **THEN** the system reports a clear error naming the model file and
  does not proceed to inference

#### Scenario: Download stalls
- **WHEN** the connection stops sending data during a model file download
- **THEN** the download fails within a bounded time, no partial file is left
  for a later run to trust, and the same clear error is reported
