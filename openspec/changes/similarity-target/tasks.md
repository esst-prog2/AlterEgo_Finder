## 1. Check the test hooks

- [x] 1.1 Find how AppTest exposes an `st.altair_chart` element in Streamlit 1.66 (element type and where the Vega-Lite spec JSON lives); verify by printing it for a two-point chart from `AppTest.from_string`, and log the accessor for design D5

## 2. Layout module (face_pipeline/target.py)

- [x] 2.1 Write `tests/test_target.py` first (design D5: exact radius, ring radius, top N named, evenly spaced named angles, same-person photos adjacent among named faces, and a score of 1.0 at radius 0); verify they fail because `face_pipeline.target` does not exist
- [x] 2.2 Implement `target_points` and `ring` per design D1 and D2; verify the 2.1 tests pass

## 3. Chart in the web UI

- [x] 3.1 Add AppTest tests to `tests/test_app.py` first: a chart is shown after a match and not on the no-face or unreadable-image pages, and after moving the threshold slider to (0.0, 0.0) the chart spec contains "high 0.0000"; verify they fail against the current app.py
- [x] 3.2 Draw the target in app.py's third result column per design D3 and D4 (layers, tooltips, equal axes, caption); verify the 3.1 tests and the whole suite pass

## 4. End-to-end check and docs

- [x] 4.1 Run `streamlit run app.py` and check the target by hand: PK.jpg on `celebrities` (closest names in the middle band, inner ring empty), the dataset switched to `celebrities_plus_me` (Me_PK inside the inner ring), a Robert_Kubica photo on `celebrities_plus_me_plus_others` (his other two photos inside the inner ring, side by side), moving the slider moves the rings, and the page stays responsive with 505 faint dots; record the observations in PLANNING_LOG.md
- [x] 4.2 README: Beat 1 and Beat 2 each gain one sentence on the target (as in proposal.md), section 3's "Final demo version" lists it, and section 4 gains "the target places each face at exactly 1 - its score from the centre, with the threshold rings"; verify the facts against 4.1 and that section 1 still has no unmeasured timing claims
- [x] 4.3 Update AGENTS.md's status and test count and the run-alterego-finder skill's test count; verify `pytest` passes in full (and with Streamlit hidden, the app tests are skipped and the rest pass); append the outcome to PLANNING_LOG.md
