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
detector scored highest. When no face is found at the image's full size, the
system SHALL retry on smaller copies of the image before reporting that no face
was detected, and SHALL still compute the embedding from the full-size image.
When the image turned by 90, 180 or 270 degrees gives the detector clearly more
confidence than the image as it is, the system SHALL use the face from the
turned image. Otherwise it SHALL treat the image exactly as if no other
orientation had been tried.

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

#### Scenario: Large face in a large photo
- **WHEN** given a large photo whose face is missed at full size but found on a
  smaller copy
- **THEN** that face is detected, with its location given in the full-size image,
  and the embedding is computed from the full-size image

#### Scenario: Face found at full size
- **WHEN** a face is found at the image's full size
- **THEN** no smaller copy is tried, and the result is the same as without the retry

#### Scenario: Large image with no face
- **WHEN** given a large image with no face, such as a blank image
- **THEN** the system reports that no face was detected

#### Scenario: Photo turned on its side or upside down
- **WHEN** given a photo of a face turned by 90, 180 or 270 degrees
- **THEN** the face is detected with its location given in the image as supplied,
  and the embedding matches the upright photo's as closely as if it had been upright

#### Scenario: Upright photo
- **WHEN** given an upright photo, where no other orientation clearly beats it
- **THEN** the result is identical to the result with no orientation check

#### Scenario: Face found only as it is
- **WHEN** a face is found in the image as it is only at full size, and a small copy of a
  turned image gives a face
- **THEN** the image is not turned

### Requirement: Embedding determinism
The system SHALL produce the same embedding vector each time it processes
the same input image.

#### Scenario: Repeated extraction is stable
- **WHEN** the same image is processed for embedding extraction twice
- **THEN** both extractions return the same 512-dimensional vector
