# Review of the two Homework 10 videos

Both: 1920 x 1080, 30 fps, silent on purpose (the course asks for a video that works without
sound, and it plays muted on the page). `hyperframes check` passes for both; the kept warnings are
`film_silent` (on purpose) and `timeline_track_too_dense` (a few timed lines per scene).

## Tour (video/tour, 32 s)
- Real screens: the running Streamlit app with the pool of 500 and a public-domain photo of Marie
  Curie (Henri Manuel, about 1920, Wikimedia Commons). Her result is real: Marco van Basten 0.2097,
  four Alter Egos, nobody at Same person. The cards' photos keep the app's own credits.
- Checked: frames at 1.5, 3.8, 4.6, 7.5, 12.5, 14.5, 17.5, 21, 25.5 and 30 s, and five frames of the
  rendered MP4.
- Weakest shot: the target's own labels stay small even at 2.4x (the app draws them at 11 px).
- The photo landing in the query box is drawn over a screenshot: dropping a file there is a real
  feature of the page, but this is a re-enactment, not a screen recording.

## Explainer (video/explainer, 32.5 s)
- Every number is measured: the fixed bar 0.2017 and 66 / 198 / 200 of 200 strangers at
  50 / 500 / 5,000 faces with average best matches 0.18 / 0.25 / 0.32 (data/spike_results.json);
  the pool's bars 0.1864 / 0.3706 and its 567 strangers (PLANNING_LOG, 2 Nov 2026).
- Which dots turn green follows a fixed seeded order: only the counts are data.
- Weakest shot: the opening question is hypothetical ("your best match"); the 0.25 is the measured
  average for 500 faces, which the crowd scene then reveals.
