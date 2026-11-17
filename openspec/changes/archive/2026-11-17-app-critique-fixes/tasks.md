## 1. Thresholds and datasets

- [x] 1.1 Remove `_threshold_slider` and its notice; label, draw and report with the dataset's calibrated thresholds; replace the four slider tests in `tests/test_app.py` with calibrated-only tests (no slider on the page, labels equal the CLI's, rings at the calibrated thresholds, report labels) and keep the no-calibration error test; verify `pytest tests/test_app.py` passes.
- [x] 1.2 Add `_dataset_label` and the `wikidata` default to the dataset selectbox; add tests for the readable names, the default and the switch without re-upload; verify they pass.

## 2. The verdict

- [x] 2.1 Add the pure function `_verdict(labeled)` and its rendering with `st.html` (escaped name, label dot, score in the display face) directly under the uploader, plus the one-line explanation of the three labels with the dataset's numbers; add tests for the three outcomes and for markup in a name (via `at.html`); verify they pass.
- [x] 2.2 Rearrange the result row: photo thumbnail and face crop in one narrow column, the target in the wide one; verify with a 1440 x 900 screenshot that the verdict line and the whole target are above the fold (the first card row follows after one scroll).

## 3. The Scoresheet structure

- [x] 3.1 Add the scoped stylesheet (one `st.html` block): the grid on the paper, 2 px navy frames on bordered containers and the upload area, capitals in the display face for headings and card names, ink score figures, navy info notices, captions in ink soft at full opacity; add a test that the block only targets the listed Streamlit test ids and the page's own classes; verify it passes.
- [x] 3.2 Make each card a bordered container with its photo as an `<img>` with alt text "Photo of <name>"; change the results heading to `st.header`; verify `pytest tests/test_app.py` passes (names, scores and labels still read as before).

## 4. Any screen

- [x] 4.1 Give the target spec a `description` with the counts per label, keep its legend inside the chart with the caption directly under it, and let the 640 x 460 canvas shrink with its column through the stylesheet; update `tests/test_target.py`/`tests/test_app.py` where they read the spec; verify they pass.
- [x] 4.2 Set `[client] toolbarMode = "viewer"` in `.streamlit/config.toml`; extend `tests/test_shared_design.py`; verify it passes.

## 5. Words

- [x] 5.1 Change the no-face error to start with "No face detected" and add the cause and what to try; update the no-face test; verify it passes.
- [x] 5.2 Update README section 3's "Final demo version" bullet (no slider on the page; overrides in the CLI) and the web-ui wording anywhere else in README that mentions the slider; verify by searching README for "slider".

## 6. Check the whole

- [x] 6.1 Run `python -m pytest tests/` and verify every test passes.
- [x] 6.2 Run the page with the DiCaprio photo on the pool and with `data/demo/no_face.jpg`; take screenshots at 1440 x 900 and 390 x 844 and verify: the verdict line, framed cards, ink scores, grid, captions at 4.5:1 or better (measured), the whole target inside 390 px with no sideways scroll, no Deploy toolbar, only localhost requested.
