## MODIFIED Requirements

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
