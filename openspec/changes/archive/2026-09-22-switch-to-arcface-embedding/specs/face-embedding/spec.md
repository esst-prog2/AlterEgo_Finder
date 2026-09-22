## MODIFIED Requirements

### Requirement: Face detection and embedding extraction
The system SHALL detect a face within an input image and, when a face is
found, SHALL produce a 512-dimensional embedding vector representing that
face's identity.

#### Scenario: Face present
- **WHEN** given an image containing a detectable face
- **THEN** a 512-dimensional embedding vector is returned for that face

#### Scenario: No face present
- **WHEN** given an image with no detectable face
- **THEN** the system reports that no face was detected and does not
  produce an embedding

### Requirement: Embedding determinism
The system SHALL produce the same embedding vector each time it processes
the same input image.

#### Scenario: Repeated extraction is stable
- **WHEN** the same image is processed for embedding extraction twice
- **THEN** both extractions return the same 512-dimensional vector
