## Why

Reading the list of 650 people showed who should not be offered as someone's alter
ego, and who is missing. The selection by fame needs curating by hand.

## What Changes

- **Left out:** Roman Polanski, Gerard Depardieu, R. Kelly and Robinho (convicted of
  sexual offences), Elie Wiesel (a Holocaust survivor, listed through a stray footballer
  tag), and "Megan Foxiana" (a garbled Wikidata name).
- **Added by hand:** Noah Wyle, Robert Kubica and Ella Purnell, ahead of the others, so
  they are in the pool. Their images pass the same licence, author and face checks.
- The pool is rebuilt from the new list and recalibrated.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `public-figure-pool`: "Committed selection of people" allows additions and exclusions
  by hand.

## Impact

- Changed: `refresh_wikidata_list.py`, `data/wikidata_people.json`, tests.
- The local `data/wikidata` pool changes; the top matches may shift.
