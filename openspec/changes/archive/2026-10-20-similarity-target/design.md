## Context

`app.py` already has everything the target needs on each rerun: `labeled`, a
ranked list of `(IndexEntry, score, label)` covering every indexed face; the
selected `(low, high)` thresholds; and the candidate count `top`. The result
area has three columns, `[2, 1, 3]`: photo, face crop, and an unused third
column. The card colours are
green for `HIGH_CONFIDENCE`, orange for `LOW_CONFIDENCE` and gray for
`NO_MATCH`. See proposal.md for why there is no projection.

## Goals / Non-Goals

**Goals:**
- Every plotted distance is exact (one minus the score), and the code that
  computes the layout is tested without Streamlit.
- The threshold bands are areas on the plot, and they move with the slider at
  no extra cost (no re-embedding, no re-ranking).

**Non-Goals:**
- Any projection or clustering of the 512-d space.
- The target inside `summary.html` (the report spec stays as it is).
- Comparing two queries on one target.

## Decisions

### D1. Layout lives in `face_pipeline/target.py`, drawing lives in `app.py`
`target_points(labeled, top) -> List[TargetPoint]`, where `TargetPoint` holds
person, score, label, `radius = 1 - score`, angle, x, y and `named`.
`ring(threshold, steps=180) -> (xs, ys)` gives the circle of radius
`1 - threshold`. Both are pure numpy and dataclasses, unit-tested directly.
`app.py` turns them into a Vega-Lite chart (D3).
*Alternative rejected:* computing everything inside `app.py`. Then the exact
distances could only be tested through AppTest's serialised chart.

### D2. Angles: two evenly spaced passes, grouped by person
1. Faces are ordered by (best rank of their person, own rank), so a person's
   photos are consecutive.
2. The **named** faces (the top N by rank, in that grouped order) are spaced
   evenly over the full circle, starting at 12 o'clock and going clockwise.
3. The **other** faces are spaced evenly over the full circle in the same
   order, offset by half a step.

Why two passes: with one pass over 505 faces, the top 10 would share about 7°
of the circle and their names would overlap. A person whose photos fall on
both sides of the top-N cut (rare) is grouped only within each pass, which is
why the spec scenario talks about "several of the top N faces".

### D3. Vega-Lite chart: layers and an equal aspect ratio
The chart is a hand-built Vega-Lite spec passed to `st.vega_lite_chart`,
with each layer's data inline (`"data": {"values": [...]}` inside the layer).
*Changed during apply (task 1.1):* the first plan was Altair, but Streamlit
sends DataFrame and top-level chart data through pyarrow, and on this machine
Windows' application control policy blocks pyarrow's DLL ("DLL load failed").
Data inline in the layers is passed through as JSON and never loads pyarrow.
It also needs no Altair. AppTest exposes the chart as
`at.get("vega_lite_chart")`, and `proto.spec` holds the JSON.

The layers, bottom to top:
1. The two rings, as `mark_line` in path order and dashed. Each is labelled
   with a constant `mark_text` such as "high 0.3643", so the label text sits
   in the chart spec, where a test can find it.
2. The other faces: `mark_circle`, gray, opacity 0.25, small.
3. The named faces: `mark_circle`, coloured like the cards, larger.
4. The names of the named faces: `mark_text`.
5. The query at the centre: a dark `mark_point` with a "you" label.

*Added after the user's first look (task 4.1), for readability on slides:*
named labels read `#1 Name (0.2146)`; fonts are 12-13 px; the centre has a
"You (query)" label; and dashed guide rays run from the centre to the top 5
faces. The tooltip adds "Distance (1 - score)". The angle is deliberately
*not* shown on hover, because it carries no meaning.
*Fixed after a blank chart in the browser:* with these additions the spec
passed Vega-Lite schema validation and AppTest, but Streamlit drew nothing.
Removing the hover-ray selection did not help. Replacing the rays' `datum`
centre (`"x": {"datum": 0}`) with plain data fields (`x0`, `y0` in each row)
did, so every position in the spec is a data field, and a test guards against
`"datum"`. The hover ray stays out: it was never seen working, and it would
need re-checking in a browser.
*Theme:* the user's Streamlit runs in dark mode, where the near-black centre,
names and ring labels were almost invisible. Their colours now come from
`st.context.theme.type`: near-black and grays in light mode, near-white and
lighter grays in dark mode, and one mid-gray readable on both while the theme
is not reported yet (`None`, e.g. in AppTest). The label colours (green,
amber, gray) read on both and are unchanged.
*Layout, after checking real screenshots in headless Chromium:* long names were
cut off at the chart's edges, ring labels on the rings collided with named
faces, and the unnamed faces formed a spiral (in rank order, distance grows
with angle, so the angle quietly encoded rank). Now: the chart is 640x460 with
the x range scaled by the same ratio (rings stay round), in a wider column
(`[1.6, 0.9, 3.5]`); names sit beside their dot, pointing outward; the rings
are explained by a legend in the top-left corner ("inner ring: high ...",
"outer ring: low ..."); and the unnamed faces are placed in a fixed order
scrambled by a CRC32 of the person's name (one person's photos still
consecutive), so they form an even cloud. The named top N keep rank order
clockwise from 12 o'clock, so they read #1, #2, ...
*Presentation, decided with the user:* the centre reads "You"; only the #1
label shows its score; the named faces' tooltips carry a 64-px JPEG data-URI
thumbnail in a field titled "image" (vega-tooltip renders it as a picture,
checked by hovering in Chromium), while the unnamed cloud stays text-only to
keep the spec small; and every confidence label is shown with a plain-language
name next to it ("Same person", "Alter Ego", "Not You"): in the three-line
legend, in the tooltips, and on the cards (name beside the score, technical
label on the next line). The legend headroom grew to 1.45x the reach so its
third line clears the circle.
*Revised with the user:* the page shows only the plain names; the technical
labels are for developers and stay in the CLI, the report and the specs (the
chart's colour scale keys off the plain names too, so they are not even in
the spec JSON). Tooltip thumbnails are 128 px. Card photos are centre-cropped
to squares (`_square_crop`), so the card text lines up. Because `_thumbnail`
is cached by Streamlit, changing `THUMBNAIL_PX` needs a server restart to take
effect.

Tooltips on layers 2 and 3 show person, score (4 decimals) and label. Both
axes are hidden and share the domain `[-R, R]`, where
`R = 1.05 * max(max radius, 1 - low)`. Width equals height, so circles stay
round. A caption under the chart says: "Distance from the centre = 1 -
similarity (exact). Direction means nothing." The chart goes in the empty
third column, next to the photo and the crop.

### D4. Edge cases
- A score of 1.0 (the query image itself is in the dataset) gives radius 0,
  on top of the centre marker. It's still named and has a tooltip.
- Negative scores give a radius above 1. `R` grows to fit them.
- Thresholds below 0 (test configs with -1) give a ring radius above 1. Also
  covered by `R`, since it includes `1 - low`.

### D5. Testing
- `tests/test_target.py`:
  - radius equals `1 - score` for every face;
  - the ring radius equals `1 - threshold` at every point;
  - exactly `min(N, faces)` faces are named, and they are the top N by rank;
  - named angles are evenly spaced;
  - photos of one person among the named faces are adjacent.
- `tests/test_app.py`:
  - a Vega-Lite chart is present after a match and absent on the no-face and
    unreadable-image pages (the element accessor is checked in task 1.1);
  - after moving the slider, the chart spec contains the new ring labels
    ("high 0.0000").

## Risks / Trade-offs

- [People read meaning into direction] → the caption says it means nothing,
  and the even spacing makes that visible (no clumps).
- [Labels of named faces overlap near the centre when several score close to
  1] → rare outside self-matches; the tooltip still separates them.
- [Vega-Lite renders differently in a later Streamlit] → only standard marks
  are used. The layout code doesn't depend on the chart library.
- [Someone later gives the chart a DataFrame or top-level data] → pyarrow loads
  and fails on machines with this app-control policy. A comment in app.py says
  why the data stays inline in the layers.
- [505 faint points slow the page] → 505 rows is small for Vega-Lite; checked
  by hand in task 4.1.

## Migration Plan

Additive. Reverting `app.py` removes the chart; `target.py` has no other users.
