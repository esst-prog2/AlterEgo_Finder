## 1. Tests first

- [x] 1.1 Write tests: `read_image` reads from an accented path, and returns None for a missing, empty or non-image file; both models load and match from an accented `MODELS_DIR`; a dataset in an accented folder keeps all its images; `match.py` runs on an accented query path; a stalled download raises `ModelWeightError` and leaves no partial file; the download passes a timeout; and the guard from design D5. See them fail, on the real behaviour

## 2. The fix

- [x] 2.1 Add `face_pipeline/images.py` and replace `cv2.imread` in `app.py`, `match.py`, `calibration.py`, `index.py` and `report.py`
- [x] 2.2 Load both models from bytes in `detector.py` and `embedder.py`
- [x] 2.3 Stream the download with a per-read timeout in `weights.py`, and update the existing tests that patch `urlretrieve`
- [x] 2.4 Mutation-check: going back to `imread`, to path-based model loading, and to no timeout must each fail a test

## 3. Proof and record

- [x] 3.1 Verify results did not move (D4): `read_image` matches `cv2.imread` on every image, rebuilt embeddings for `data/celebrities` and `data/wikidata` and calibration are byte-identical, and `PK.jpg` still gives Psy 0.2702 and `Me_PK` 0.4322
- [x] 3.2 Copy the repository to an accented temporary folder: run the full tests there, `match.py`, and in Chromium the page with `PK.jpg` on `wikidata`. Delete the copy afterwards
- [x] 3.3 Update AGENTS.md and the skill's ASCII notes and test counts, verify `pytest` in full and with Streamlit hidden, and append the outcome to PLANNING_LOG.md
