# Review of the two Homework 10 videos

Both: 1920 x 1080, 30 fps. The explainer is silent; the tour has music ("Carefree", Kevin MacLeod,
CC BY 4.0) but starts muted on the page and tells its story in captions, so it works without sound.
The music was measured (music, onset 0.17 s, fades out by 29.9 s), not heard. `hyperframes check` passes for both; the kept warnings are
`film_silent` (on purpose) and `timeline_track_too_dense` (a few timed lines per scene).

## Tour (video/tour, 30 s), second version
- Story: "Brad Pitt or Leonardo DiCaprio?" The query is a second photo of DiCaprio (Presidencia de la
  Republica Mexicana, 2017, CC BY 2.0, Wikimedia Commons), not the pool's own photo of him. The real
  result: DiCaprio first at 0.6867 (Same person, the one face inside the ring), then Matt Damon
  0.2678, Keke Rosberg 0.2672, Oliver Kahn 0.2286 and Brad Pitt 0.2109 (Alter Ego). The cards keep
  the app's own photo credits.
- Chosen from 13 well-known pool members tested with other openly licensed Commons photos; a photo
  with private people in the background was ruled out.
- The first version (Marie Curie, nobody at Same person) was replaced because it could not show all
  three labels.
- Checked: snapshots at 1.5, 4.6, 7.5, 12, 15, 18, 21.5, 26 and 30.5 s, and six frames of the MP4.
- Third pass: a logo (the app's target in miniature) on every scene, a score key under the target,
  music.
- Kept warnings: the two credit lines are on screen shorter than a full read; they are credits.
- The photo landing in the query box is re-enacted over screenshots: dropping a file there is a
  real feature of the page, but that moment is not a screen recording.

## Explainer (video/explainer, 32.5 s)
- Every number is measured: the fixed bar 0.2017 and 66 / 198 / 200 of 200 strangers at
  50 / 500 / 5,000 faces with average best matches 0.18 / 0.25 / 0.32 (data/spike_results.json);
  the pool's bars 0.1864 / 0.3706 and its 567 strangers (PLANNING_LOG, 2 Nov 2026).
- Which dots turn green follows a fixed seeded order: only the counts are data.
- Weakest shot: the opening question is hypothetical ("your best match"); the 0.25 is the measured
  average for 500 faces, which the crowd scene then reveals.
