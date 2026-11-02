## 1. The list

- [x] 1.1 Tests first for hand-picked people (first on the list, not repeated, counted in the total) and for the committed list's content; see them fail, then implement in `refresh_wikidata_list.py`; verify they pass
- [x] 1.2 Regenerate `data/wikidata_people.json`; verify the three additions are on it and the six exclusions are not

## 2. The pool

- [x] 2.1 Run `setup_data.py --wikidata`; verify 500 images, the excluded people gone, each addition saved or its skip reason reported, new thresholds written and other data unchanged
- [x] 2.2 Remeasure `PK.jpg`'s top matches and the self-match against the new thresholds, in Chromium; report the numbers
- [x] 2.3 Run the full test suite; update the log
