## 1. Names

- [x] 1.1 Add `_display_name` and use it in the verdict, the cards' name line and alt text, and the target's names and tooltips; update `_cards`/CLI comparisons and the markup-name tests in `tests/test_app.py`; add a test that "Leonardo_DiCaprio" reads "Leonardo DiCaprio" in the verdict, card, target and alt text; verify `pytest tests/test_app.py` passes.

## 2. Datasets and the primary action

- [x] 2.1 Order the dataset list public-first and add the "Public datasets first" test; verify it passes.
- [x] 2.2 Make the report download `type="primary"`, add the upload-hint and file-size rules to the stylesheet and its id test; add a test that the download is primary; verify `pytest tests/test_app.py` passes.

## 3. Report labels

- [x] 3.1 Show "Same person (HIGH_CONFIDENCE)" etc. in `face_pipeline/report.py`; update `tests/test_report.py` (dots test, plain-name test); verify `pytest tests/test_report.py tests/test_match_cli_report.py` passes.

## 4. Check

- [x] 4.1 Run `python -m pytest tests/` and verify every test passes.
- [x] 4.2 In a browser with the DiCaprio photo: the verdict reads "Leonardo DiCaprio", the dataset list starts with the public datasets, the download is navy, the upload hint and file size measure at least 4.5:1, the report preview shows "Alter Ego (LOW_CONFIDENCE)"; only localhost contacted.
