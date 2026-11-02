## 1. The committed dataset list

- [x] 1.1 Generate `data/lfw_split.json` once from today's `data/celebrities/` and `data/calibration/` folders; verify every listed file exists in `data/lfw/lfw.tgz` under `lfw/<path>` and is byte-identical to the local copy, and that it is not gitignored (`git check-ignore`). If any file differs or is missing, stop and report it
- [x] 1.2 Record the archive's real size and the time setup takes for the README (replacing the proposal's "about 170 MB" if it differs)

## 2. Setup script

- [x] 2.1 Write `tests/test_setup_data.py` first (design D6, using a tiny archive and split list built from fixtures); verify they fail because `setup_data` does not exist
- [x] 2.2 Implement `setup_data.py`: verified download with `.part` and a timeout (D3), extraction of only the listed files (D2), calibration through `calibrate.main` with skip and `--recalibrate` (D4), `--tarball` and `--data-dir` (D3, D5), and a clear error and exit 1 on every failure; verify the 2.1 tests pass
- [x] 2.3 Mutation-check the safety behaviour: skipping the checksum check, and always recalibrating, must each fail a test; restore and verify the whole suite passes

## 3. Web UI message

- [x] 3.1 Update the no-indexed-dataset test first to expect `setup_data.py` as well as `match.py`, see it fail, then change the message in `app.py`; verify the app tests pass and, in Chromium with an empty data folder, the message is readable

## 4. Fresh-clone proof

- [x] 4.1 `git clone` the branch into the scratchpad and run the README's steps there with a new virtual environment: install, `python setup_data.py` using the real download, `streamlit run app.py` on a spare port. In Chromium, drop `data/my_photo/PK.jpg` and verify Jean-Sebastien_Giguere is first at 0.2146, labelled Alter Ego, the same as README section 1, and that `data/config.json` holds the same thresholds as this checkout. Report anything that needed a step the README lacks, and fix the README
- [x] 4.2 In that clone, run `python setup_data.py` a second time; verify it finishes quickly without downloading and `config.json` is unchanged; delete the clone afterwards
- [x] 4.3 In this checkout, run `python setup_data.py`; verify it changes nothing (`git status` clean apart from this change, the same `config.json`, and `data/celebrities_plus_me*` and `data/my_photo*` untouched)
- [x] 4.4 Walk through the three README beats in Chromium in this checkout to verify the demo still works

## 5. Docs and record

- [x] 5.1 README: a "Getting started" section (install, setup, run, time and disk use), how to recreate Beat 2 with two photos of your own, a Windows application-control troubleshooting note, and section 5's privacy note mentioning the LFW download; verify each command by having run it in 4.1
- [x] 5.2 Update AGENTS.md's status and test count and the run-alterego-finder skill; verify `pytest` passes in full and, with Streamlit hidden, that the app tests are skipped and the rest pass
- [x] 5.3 Append the outcome to PLANNING_LOG.md (tests, red/green evidence, fresh-clone result)
