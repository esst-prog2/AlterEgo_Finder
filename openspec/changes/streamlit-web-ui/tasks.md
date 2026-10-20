## 1. Setup

- [x] 1.1 Add `requirements-ui.txt` (`-r requirements.txt`, `streamlit>=1.40,<2`) and install it; verify `python -c "import streamlit; print(streamlit.__version__)"` prints a version in range, check whether `streamlit.testing.v1.AppTest` can drive `file_uploader` in that version, and log which D9 test route applies
- [x] 1.2 Add `.streamlit/config.toml` as in design D7; verify by reading it back that `server.address = "localhost"`, `maxUploadSize = 10` and `gatherUsageStats = false` are set
- [x] 1.3 Add `data/demo/no_face.jpg` (300x300 white); verify `extract_embedding(cv2.imread("data/demo/no_face.jpg"))` raises `NoFaceDetectedError`

## 2. Shared matching module (refactor, no CLI behavior change)

- [x] 2.1 Add `detect_and_align` to `face_pipeline/embedder.py` and rewrite `extract_embedding` on top of it; verify the existing 60 tests pass
- [x] 2.2 Write `tests/test_match_image.py` first (`load_thresholds` with missing, broken and valid config.json; `classify` boundaries via `face_pipeline.matching`; `match_image` on `tests/fixtures/dataset` with `obama_query.jpg` ranks the Obama photos above Biden and returns a 112x112 aligned crop; `embed_query` on a blank image raises `NoFaceDetectedError`); verify they fail because `face_pipeline.matching` does not exist yet
- [x] 2.3 Implement `face_pipeline/matching.py` per design D1; verify the 2.2 tests pass
- [x] 2.4 Switch `match.py` to `load_thresholds` and `match_image`, re-importing `classify` and the label constants; verify all 60 existing tests pass unchanged, and that `match.py --image data/my_photo/PK.jpg --dataset data/celebrities` prints the same 10 lines as on 2026-10-16 (Jean-Sebastien_Giguere 0.2146 LOW_CONFIDENCE first)
- [x] 2.5 Make `render_report` accept `Path | np.ndarray` (design D5), with a test that an array query renders the same embedded query image as the path form; verify the existing report tests still pass

## 3. Web UI (app.py)

- [x] 3.1 Dataset dropdown per design D3, plus the "index a dataset first" message when none is indexed; AppTest tests: only folders with `.matchcache/embeddings.npy` are listed (built in tmp_path), and an empty `data/` shows the message with no uploader
- [x] 3.2 Threshold range slider per design D4: preset from `<dataset parent>/config.json`, override notice, and the "run calibrate.py" error when thresholds are missing; AppTest tests for preset values, notice shown only after moving a handle, and the missing-config error
- [x] 3.3 Upload, decode and result cards per design D6 and D9 (`show_results`): aligned crop next to the photo, top N cards (default 10, 1-20), names rendered as plain text, "No face detected" and unreadable-image errors with no cards; tests: 10 cards on a dataset of 12 faces, same order, scores and labels as `match.py` on the same inputs, no-face and garbage-bytes cases show the error and no cards, and a folder name containing `<script>` shows up as literal text
- [x] 3.4 Report preview and download (design D5): the report is written to `data/results/summary.html` and offered via a download button and an inline preview; tests: download data is a self-contained HTML containing each shown candidate's label, it changes when the thresholds change, and no report is offered on the no-face error

## 4. End-to-end check and docs

- [x] 4.1 Run `streamlit run app.py` from the repository root and walk the README section 1 beats: PK.jpg on `celebrities` (top card Jean-Sebastien_Giguere 0.2146 LOW_CONFIDENCE), switch to `celebrities_plus_me` without re-uploading (Me_PK first, 0.4322 HIGH_CONFIDENCE), drop `data/demo/no_face.jpg` ("No face detected"); verify each against PLANNING_LOG.md (screenshots for the slides are deferred to the slides work, decided 2026-10-20)
- [x] 4.2 While the app runs, verify with `netstat -an | findstr 8501` that it listens only on 127.0.0.1 / ::1, not 0.0.0.0
- [x] 4.3 Update README section 4 with the UI's acceptance criteria and a how-to-run line (`pip install -r requirements-ui.txt`, `streamlit run app.py` from the repo root), update AGENTS.md's status and test count, and the run-alterego-finder skill if its steps changed; verify `pytest` passes in full with Streamlit installed, and with it uninstalled the app tests are skipped while the rest pass
- [x] 4.4 Append the outcome (test counts, red/green evidence, the 4.1 scores) to PLANNING_LOG.md
