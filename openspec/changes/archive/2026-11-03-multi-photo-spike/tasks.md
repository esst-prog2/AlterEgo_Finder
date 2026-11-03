## 1. Setup and tests

- [x] 1.1 Add `data/spike_multiphoto/` to `.gitignore` and confirm with `git check-ignore`, before the folder exists
- [x] 1.2 Write `tests/test_spike_multiphoto.py` for the pure parts: the four arms' scores, the varied photo pick, and the walk on small synthetic vectors (moves to better, stops when none is better, respects the step limit, counts faces checked). See them fail
- [x] 1.3 Implement those parts in `spike_multiphoto.py`, reusing `wikidata_pool.py`'s requests and licence rules and `calibration.py`'s threshold fit. Verify the tests pass, and that breaking the averaging's normalisation or the walk's stop rule fails one

## 2. Fetch

- [x] 2.1 Write the gallery selection (design D1) and record the chosen people. Log the predictions and decision rule from D6 in PLANNING_LOG.md before any result exists
- [x] 2.2 Fetch photos (D2) on a thin run of 5 people, check no request carries anything but Wikimedia names, then run all of them. Honour rate limits, resume if stopped, and record how many photos each person got and why others were rejected

## 3. Measure

- [x] 3.1 Run the four arms (D3, D4) at floors 0.25, 0.15 and 0.35: same-person hits and misses at each arm's fitted threshold, thresholds, held-out strangers reaching *Same person*, and `PK.jpg`'s top matches with labels
- [x] 3.2 Run the walk (D5) for k = 5, 10 and 20, on `PK.jpg`, 200 strangers and 100 people with a second photo in the graph
- [x] 3.3 Write `data/spike_multiphoto_results.json`, and confirm it holds only scores, counts and public figures' names

## 4. Proof and record

- [x] 4.1 Apply the decision rule from D6, and compare the result with each prediction, including the wrong ones
- [x] 4.2 Confirm nothing under `data/spike_multiphoto/` or any private photo is tracked, the program's `data/wikidata` and config files are unchanged, and `pytest` still passes in full and with Streamlit hidden
- [x] 4.3 Update AGENTS.md and the skill's test counts, and append the outcome to PLANNING_LOG.md
