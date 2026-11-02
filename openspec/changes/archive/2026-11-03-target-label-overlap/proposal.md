## Why

In README's Beat 2, the moment the system recognises the real person, the target's
`#1 Me_PK (0.4322)` label runs into `#2 Psy` and is hard to read. It will happen on any
self-match: the top face sits much closer to the centre than the next one, so its name,
pointing right from 12 o'clock, crosses the next dot. The same picture goes on the slides
due 2026-11-28, so it should be readable.

## What Changes

- A named face's label moves to another side of its dot when the usual place, beside the
  dot and pointing outward, would hit another label, another named face, the ring legend
  or the chart's edge.
- Dots do not move: distances stay exactly one minus the score, and angles stay as they are.
- Labels that do not collide stay where they are today, so Beat 1's picture is unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-ui`: "Similarity target" gains a requirement that names stay readable, with a
  scenario for the default 10 names and one for crowded charts.

## Impact

- `face_pipeline/target.py` (a pure placement function), `app.py` (`_target_spec` draws the
  labels by placement), `tests/test_target.py`, `tests/test_app.py`.
- No new dependencies. README section 1's text stays true as written, so the Canvas text
  does not change.
