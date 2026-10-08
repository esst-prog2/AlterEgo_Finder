# face-embedding Specification

## Purpose

Detects a single face in an image and produces a fixed-length numeric
embedding vector that captures facial identity, usable for similarity
comparison between faces.

## Requirements

### Requirement: Face detection and embedding extraction
The system SHALL detect a face within an input image and, when a face is
found, SHALL produce a 512-dimensional embedding vector representing that
face's identity. When more than one face is detected, the system SHALL use
the largest face by bounding-box area, regardless of which face the
detector scored highest.

#### Scenario: Face present
- **WHEN** given an image containing a detectable face
- **THEN** a 512-dimensional embedding vector is returned for that face

#### Scenario: No face present
- **WHEN** given an image with no detectable face
- **THEN** the system reports that no face was detected and does not
  produce an embedding

#### Scenario: Several faces present
- **WHEN** given an image containing several detectable faces, where a
  smaller face has a higher detector score than a larger one
- **THEN** the larger face is the one detected and embedded

#### Scenario: Subject wearing sunglasses with a printed face on clothing
- **WHEN** given a photo of a person wearing sunglasses, head slightly
  turned, whose T-shirt shows a printed face
- **THEN** the person's own face is detected, not the printed one

### Requirement: Embedding determinism
The system SHALL produce the same embedding vector each time it processes
the same input image.

#### Scenario: Repeated extraction is stable
- **WHEN** the same image is processed for embedding extraction twice
- **THEN** both extractions return the same 512-dimensional vector
