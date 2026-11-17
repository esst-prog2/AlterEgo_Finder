## Why

Impeccable's critique of the restyled page scored it 24/40 (`.impeccable/critique/2026-11-17T10-26-42Z__app-py.md`). The page never states its answer: after an upload, "#1 Leonardo DiCaprio, Same person, 0.6867" is a 12 px label on the chart and the cards start below the fold. Only DESIGN.md's colours reached the page, not its frames, grid and type, so the page and its own embedded report look like two products. Captions fail contrast, the target is clipped on a phone, the no-face error is a dead end, and an expert control (the threshold override) sits beside the first-time choice.

## What Changes

- A **verdict line** right under the uploader states the result in one sentence with its plain label: the closest face, its score and label; or that nobody in the dataset reaches Same person and who the closest Alter Ego is; or that nobody is close (Not You). The query photo shrinks to a thumbnail beside the face crop, so the target takes the row.
- The page takes **DESIGN.md's structure**, not only its colours: the paper's 24 px grid, 2 px navy frames on the result cards and the uploader, uppercase condensed headings and card names, the score as ink display figures instead of small green code, a navy info box.
- **Readable on any screen**: captions at 4.5:1 or better, the target scaled to fit a 390 px screen, an accessible description of the target, alt text on card photos, heading levels in order (h1 then h2), Streamlit's Deploy/menu toolbar hidden.
- **Plain words**: the no-face error keeps "No face detected" and adds the likely cause and what to try; datasets get readable names (the folder name stays visible, as README section 1 names folders), and the public-figure pool is selected by default when it is indexed; the page says what Alter Ego means.
- **BREAKING (page only):** the threshold slider is removed. The page always uses the dataset's calibrated thresholds; overriding them stays a CLI option (`match.py --threshold-low/--threshold-high`). Labels, scores, matching, the CLI, the report and privacy do not change.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `web-ui`: the threshold control is removed (calibrated thresholds only); the similarity target and report requirements no longer refer to a slider; the no-face error gains guidance; dataset selection gains readable names and a default; the shared-look requirement gains the structure (grid, frames, condensed type, score figures); new requirements for the verdict line and for reading on any screen.

## Impact

- `app.py`: verdict line, layout of the photo/crop/target row, dataset names and default, removal of `_threshold_slider`, one scoped stylesheet, card rendering, chart description and width, error copy.
- `.streamlit/config.toml`: `[client] toolbarMode`.
- `tests/test_app.py`: slider tests replaced by calibrated-only and verdict tests; new tests for dataset names, error copy and the stylesheet; `tests/test_shared_design.py` extended.
- `README.md` section 3 ("Final demo version") bullet that describes the slider; section 1 is unchanged (its folder names stay visible in the dropdown).
- The tour video's app screens would need capturing again for the page to match the video exactly (not part of this change).
