## MODIFIED Requirements

### Requirement: Dataset selection
The web UI SHALL offer a dropdown of the folders directly under `data/` that
already have an embedding index, and SHALL match against the selected one.
Changing the selection SHALL re-run the match on the photo already uploaded.

#### Scenario: Only indexed datasets listed
- **WHEN** `data/` holds folders with an embedding index and folders without
  one
- **THEN** the dropdown lists only the folders with an index

#### Scenario: Dataset switched without re-upload
- **WHEN** a photo is uploaded and the user selects a different dataset
- **THEN** the page shows the results of that same photo against the newly
  selected dataset, without a new upload

#### Scenario: No indexed dataset
- **WHEN** no folder under `data/` has an embedding index
- **THEN** the page tells the user to run the setup command, or to index a
  dataset of their own with the CLI, and offers no upload
