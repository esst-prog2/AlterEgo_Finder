## Context

`target_points` places the top N at evenly spaced angles, clockwise from 12 o'clock, at
radius `1 - score`. `_target_spec` then draws each name beside its dot, pointing outward:
left-aligned on the right half, right-aligned on the left. The #1 face has `x = 0`, so its
name, which also carries the score, runs right at the dot's height.

In Beat 2 the chart is 640 by 460 px with about 129 px per unit, since the faint cloud reaches
a score of about -0.23. `Me_PK` (radius 0.57) is at about (320, 157) with its name from 329 to
about 430. `Psy` (radius 0.73, 36 degrees) is at about (376, 154), right on that name. In Beat 1, `Psy` is #1 at radius 0.73, so its dot sits
higher and nothing collides. The trigger is a #1 face much closer than the #2 face.

## Goals / Non-Goals

**Goals:**
- With the default 10 names, no name overlaps a name, a named dot, the ring legend or the
  chart's edge, on real data and across varied scores.
- Pictures with no collision do not change.

**Non-Goals:**
- Moving dots or changing angles.
- Avoiding the faint unnamed cloud or the rings, which names already cross legibly.
- A perfect result at N = 20: the slider allows it, but it may not all fit.

## Decisions

### D1: Move the name, not the dot

Radius carries the meaning and must stay exact. Angle carries none, so changing the angles
would be allowed, such as starting at half a step. But that changes every picture, does not
rule out collisions in general, and loses "clockwise from 12 o'clock, read #1, #2, ...".

### D2: Greedy placement in rank order, eight candidate places

For each named face in rank order, try outward beside the dot (today's place), then above,
below, inward beside it, and the four places above or below shifted sideways. The shifted ones
were added during implementation: with only the first four, 6% of varied 10-name charts still
collided, as a long #1 name centred at 12 o'clock can reach the dots on both sides. Take the first place that hits nothing placed so far, all named
dots, the legend or the edge. If none is free, take the place with the least overlapping
area, so every name is still drawn. Rank order gives #1 first choice. All named dots are
obstacles from the start, which is what moves `Me_PK`'s name off `Psy`'s dot.

It is deterministic, so the same inputs give the same picture, and about 30 lines.

### D3: A pure function in `face_pipeline/target.py`, working in chart pixels

It takes the points, labels' text, the scale and the legend's box, and returns a placement
per face, so it can be tested without Streamlit. `_target_spec` loops over placements instead
of the two sides, drawing one text layer for each, since Vega-Lite's `align` and offsets are
set per mark. Every name layer keeps a `dx` (0 where centred), as the existing test tells
names from legend lines that way.

### D4: Estimate text width

The chart is drawn in the browser, so Python can't measure text. Use 6 px per character at
font size 12, against 5.9 px measured over the pool's names in Chromium, and a 12 px line height,
against 11 px measured. The 7 and 14 px first planned made every box bigger than what is drawn,
and a tenth of varied charts reported collisions. Unusually wide names can run a little past
their box, so Chromium checks real names.

## Risks / Trade-offs

- **A name above its dot can sit over a ring or some cloud.** Names already do that. It reads
  fine, and Chromium will confirm it.
- **Crowded charts may still overlap at high N.** The tests report how often at N = 20. It is
  accepted as long as the default is clean, and the result is logged either way.
