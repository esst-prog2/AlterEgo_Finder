## Why

The roadmap asked for an "embedding map" showing where the user's face lands
among the dataset faces. A read-only spike on the 505-face
`data/celebrities_plus_me_plus_others` index (PLANNING_LOG.md, 2026-10-20)
showed that a 2D projection would mislead. PCA keeps 3.3% of the variance;
distance on the map correlates with true cosine distance at only 0.19; and
`PK.jpg`'s true #1 match (Me_PK, 0.432) is the 168th nearest point on the map.
What the demo needs to show is "how close is each face to mine, and which
side of the thresholds does it fall on". That can be drawn exactly, without
any projection.

## What Changes

- **New "similarity target" plot in the web UI**, shown for every successful
  match next to the uploaded photo:
  - the query face at the centre, and each indexed face at a distance of
    exactly `1 - similarity score` from it;
  - the angle carries no meaning: faces are spread evenly in rank order, and
    several photos of one person sit side by side. A caption says so;
  - two rings at the current low and high thresholds, so the
    `HIGH_CONFIDENCE` / `LOW_CONFIDENCE` / `NO_MATCH` bands are areas on the
    plot; the rings move with the threshold slider;
  - the top N candidates (the same N as the cards) highlighted and named, and
    every other indexed face as a faint unlabeled dot;
  - hovering a point shows the person, the score and the label.
- Not shown when the photo has no face or cannot be read, like the cards.
- **README section 1**: Beat 1 and Beat 2 each gain one sentence on the target
  (Beat 1: my face at the centre, the closest celebrities in the middle
  `LOW_CONFIDENCE` band; Beat 2: Me_PK inside the inner `HIGH_CONFIDENCE`
  ring). Section 3's "Final demo version" lists the target, and section 4
  gains its acceptance criterion. This is the section 1 that is handed in on
  Canvas by 2026-11-07.
- The HTML report and the CLI are unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-ui`: one new requirement, "Similarity target" (exact distances,
  threshold rings that follow the slider, top N named, no target on error
  pages). The existing requirements are unchanged.

## Impact

- New: `face_pipeline/target.py` (the point layout, without Streamlit, so it
  can be tested directly), plus tests for it and for the plot in the app.
- Changed: `app.py` (draws the target in the currently empty third column next
  to the photo and face crop), `README.md` sections 1, 3 and 4.
- No new dependency: the chart is a plain Vega-Lite spec given to
  `st.vega_lite_chart`, with the data inline (not Altair or a DataFrame,
  because Windows' application control blocks pyarrow here; see design D3).
- `summary-report`, `face-matching-cli` and the CLI's output are untouched.
