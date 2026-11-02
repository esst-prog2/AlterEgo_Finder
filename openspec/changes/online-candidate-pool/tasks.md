## 1. The list

- [x] 1.1 Write tests for the selection logic first (round-robin order, unlabeled and under-18 people dropped, duplicates removed, illegal folder characters removed, a failed query leaves the list unchanged), see them fail, then implement `refresh_wikidata_list.py` with retries; verify they pass
- [x] 1.2 Generate `data/wikidata_people.json` (about 650 people); verify counts per occupation, no Q-number names, nobody born after the cutoff, no duplicate folders, and read the top of the list for anything that looks wrong

## 2. Thresholds per dataset

- [x] 2.1 Tests first for `config_path_for` (own file wins, else parent), in the CLI and on the page; see them fail, implement, and verify the existing threshold tests still pass unchanged
- [x] 2.2 Tests first for overlap exclusion in `calibrate.py` (names matched ignoring case, accents and underscores; excluded from strangers only; the low threshold unchanged); see them fail, implement, verify they pass
- [x] 2.3 Run `calibrate.py` on the real LFW data with `--config-out` to a scratch file; verify it is byte-identical to `data/config.json`

## 3. Thin path: 100 people

- [x] 3.1 Tests first for `face_pipeline/wikidata_pool.py` with a fake network (licence allowlist, HTML stripped from authors, wrong host not fetched, size cap, no-face skipped, 429 waits then stops with a resume message, resume refetches nothing, limit respected, attribution for every image, skip list honoured); see them fail, implement, verify they pass
- [x] 3.2 Add `--wikidata` and `--wikidata-limit` to `setup_data.py`, gitignore `data/wikidata/`, with tests that basic setup is unchanged, the pool gets its own `config.json`, and `data/config.json` is untouched
- [x] 3.3 Run the real build with `--wikidata-limit 100`; interrupt it once and resume; verify 100 images, no 429 stop, `data/config.json` and existing datasets unchanged (hash before and after), and the skipped counts by reason. In Chromium: the dataset is listed, and `PK.jpg` gets cards. Report anything surprising before scaling up

## 4. Attribution

- [x] 4.1 Tests first for `face_pipeline/attribution.py` and for `render_report` (author, licence and link shown; HTML escaped; no attribution means no line; non-Commons URL not linked); see them fail, implement, have `match.py` pass attribution; verify existing report tests still pass
- [x] 4.2 Tests first for cards and tooltips (author and licence shown as plain text, link only for Commons URLs, LFW cards unchanged); see them fail, implement in `app.py`; verify in Chromium in dark and light mode that the cards stay readable, and that no `"datum"` or pyarrow crept in

## 5. Full pool and proof

- [x] 5.1 Run the full build (500) in the background; verify 500 images and the reported skips, and record `threshold_high` for this size
- [x] 5.2 Verify matching stays offline: with the built pool, block network use in a test or run, and get results
- [x] 5.3 Measure in Chromium: `PK.jpg`'s top matches on the pool, Kubica's photos on a pool copy, and the same-person scores from the spike's overlapping people against the pool's threshold; look at the top matches for bad images. Report the numbers, since they decide whether section 1 moves
- [x] 5.4 Walk through README's three beats on LFW in Chromium; verify they are unchanged

## 6. Docs and record

- [x] 6.1 README sections 3 (the "live downloads" item narrowed: built once, never at match time), 5 (the privacy note) and 6 (how to build the pool, with time and disk); verify each command was actually run
- [x] 6.2 Update AGENTS.md and the run-alterego-finder skill; verify `pytest` passes in full, and with Streamlit hidden
- [x] 6.3 Append the outcome to PLANNING_LOG.md (tests, red/green, build numbers, the 5.3 measurements)
