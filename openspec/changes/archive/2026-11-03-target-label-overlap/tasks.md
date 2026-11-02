## 1. Tests first

- [x] 1.1 In `tests/test_target.py`, test placement directly: Beat 2's real scores give no overlap; a name with nothing in its way stays outward; a blocked name moves to the first free place in order; with no free place, the least overlapping place is taken; the result is deterministic; radii and angles are untouched
- [x] 1.2 In `tests/test_app.py`, compute name boxes from `_target_spec`'s own layers: Beat 2's scores and a sweep of varied scores (random with a fixed seed, including a #1 much closer than #2) with 10 names have no overlap with names, named dots, the legend or the edge, and every name is drawn exactly once. See them fail on today's code

## 2. The fix

- [x] 2.1 Implement the placement function in `face_pipeline/target.py` (design D2-D4)
- [x] 2.2 Draw names by placement in `_target_spec` in `app.py` (D3), and update the existing test's "names point outward" check to cover moved names only as far as it must. Verify all tests pass
- [x] 2.3 Mutation-check: always using the outward place, leaving named dots out of the obstacles and leaving out the legend must each fail a test
- [x] 2.4 Report how many charts in the sweep still overlap at 20 names

## 3. Proof and record

- [x] 3.1 In Chromium, on a separate port: Beat 2's two names are readable; Beat 1's picture is unchanged from `demo_beat1_target.png`; `celebrities`, `celebrities_plus_me` and 20 names look right; check light and dark themes
- [x] 3.2 Confirm README section 1 still holds as written, then update AGENTS.md and the skill's test counts, verify `pytest` in full and with Streamlit hidden, and append the outcome to PLANNING_LOG.md
