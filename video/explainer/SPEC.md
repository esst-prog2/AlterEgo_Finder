# Explainer: why one fixed bar fails

GOAL:    a viewer understands one idea: a similarity score means little until you know how many faces
         it was the best of, so AlterEgo Finder fits its bars to its dataset's size.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, silent (it plays muted on the promo page).
TIME:    about 32 s x 30 fps = 960 frames.
LOOK:    the promo page's scorecard world, as in ../tour/SPEC.md: ground #f4f7fb with a 40 px printed
         grid; ink #1f2328; rule navy #1d3c78. Label colours only for labels: #1a7f37 Same person,
         #d4a72c Alter Ego, #8c959f Not You. Barlow Condensed 700 uppercase for lines (64-130 px),
         Barlow 500 for small print (28-40 px). No photographs.
OBJECTS: one score ruler (0 to 0.5, x = 160 + 3200 * score, at y = 700) that every scene shares;
         a dot for "your best match"; a fixed bar; 200 dots for 200 strangers; the calibrated zones.
DATA:    every number is measured. Fixed bar 0.2017 (1% of pairs of strangers reach it) and the
         strangers' results at 50 / 500 / 5,000 faces: 66 / 198 / 200 of 200 reach it, average best
         match 0.18 / 0.25 / 0.32 (data/spike_results.json, LFW, 1 Oct 2026). The pool's bars
         0.1864 / 0.3706 and 567 strangers: 0.9% Same person, 97.0% Alter Ego (PLANNING_LOG 2 Nov 2026).
         Which of the 200 dots turn green is drawn in a fixed order; only the counts are data.
MOTION:  as the tour: enter expo.out, camera power2.inOut, exit power3.in; per-word blur-in.
SHOTS:
  0-4.5 s    question  "Your best match scores 0.25." The dot drops onto the ruler. "Is that you?"
  4.5-10.5 s bar       a bar rises at 0.2017: "One fixed bar." "Only 1 in 100 pairs of strangers reach
                       it." The right side turns green: "So 0.25 means same person?"
  10.5-21 s  crowd     200 dots, 200 strangers who are not in the dataset. 50 faces: 66 turn green, 33%.
                       500 faces: 198, 99%, average best 0.25, like yours. 5,000 faces: 200, 100%.
  21-27.5 s  fix       the ruler again, with the pool's zones: grey, gold, green. The dot lands in gold.
                       "567 strangers: 0.9% reach Same person; 97% land in Alter Ego."
  27.5-32.5 s end      "A score means little without the size of the crowd." Name and address.
BANNED:  dark void; glow; gradients; glass; KPI grid; three cards in a row; bullet slides; an invented
         distribution drawn as if measured; text moving while read.
QA:      t=2.5, 8.5, 13.5, 16.5, 19.5, 25.5, 31.
