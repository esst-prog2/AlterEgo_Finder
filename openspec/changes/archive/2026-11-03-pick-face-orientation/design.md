## Context

`detect_face` runs `_find_faces`, which tries the image at full size and then smaller copies, picks
the largest face, and returns its box and landmarks in the image's coordinates. `align_face` warps
the image with a similarity transform from those landmarks, so it already straightens any rotation
as long as the landmarks are right. The box is not used outside `detector.py` and tests.

Measured, read-only, on LFW:

| Rotation | Face found | Median same-person score | Reaching 0.3706 |
|---|---|---|---|
| 0 | 150/150 | 0.672 | 148 |
| 20 | 150/150 | 0.609 | 129 |
| 30 | 148/150 | 0.515 | 98 |
| 45 | 117/150 | 0.209 | 31 |
| 90 | 21/150 | 0.002 | 0 |
| 180 | 97/150 | -0.005 | 0 |
| 270 | 17/150 | 0.047 | 0 |

Detector score over 300 upright photos: upright median 0.929, lowest 0.874. Upright was the highest
of the four every time, and no other orientation came within 0.024 of it. Upside-down was found
206 times of 300, with a median of 0.857.

## Goals / Non-Goals

**Goals:**
- A photo turned by 90, 180 or 270 degrees matches about as well as upright.
- Every image that is not turned gets byte-identical results, because it takes today's path.
- Measure the cost: time, and false faces in images with no face.

**Non-Goals:**
- Tilts between the right angles, such as 45 degrees. That would mean many more passes, and more
  false faces, for a rarer case.
- A new message on the page, or any new setting.

## Decisions

### D1: Decide on a small copy, then use today's path

`_choose_turn(image)` runs YuNet on a copy no larger than 640 px on its longest side, turned each of
the four ways, and takes the most confident face's score in each, of any size. The first version used the
largest face's score, as a turned photo's embedding uses, but over all of LFW that wrongly turned two
upright group photos: the largest face was a bystander cut off at the edge, with a low score. If that picks a turn, the turned full
image goes through today's `_find_faces`. If not, the original does, so upright photos follow the
same code as now and cannot change.

Full-size passes in all four orientations would mean up to 16 passes on a 3000 px photo, as each runs
its own retries. Comparing at one small size is also fairer, since YuNet's scores change with size.

### D2: Turn only on a clear win

Turn only if a turned score beats upright's by more than `TURN_MARGIN = 0.02`. The lowest gap in the
measurement was 0.024, so this should still correct upside-down photos, and it leaves real photos
some room. The value is checked in task 2.3 against every image we have, and may need adjusting.

### D3: A missing upright face does not automatically mean turn

Tiny faces can be missed on the small copy, and any turned copy might then give a false face. So when
upright finds nothing on the copy, today's `_find_faces` runs on the original first. Only if that also
finds nothing does a turned face count. This also keeps the large-face fix working: those photos get
no upright face on the small copy only if they really have none.

### D4: Map the result back

Box and landmarks are mapped from the turned image to the image as supplied, as the large-face fix
does for scale. Alignment then warps the original image, with no change to `align_face`. Landmark order
stays the same, as a turn is not a reflection.

### D5: Fixed before the run

Expected: turned photos at 90, 180 and 270 reach at least 120 of 150 at 0.3706, against 148 upright.
No image in `data/celebrities`, `data/wikidata`, `data/calibration` or the fixtures turns, so embeddings
and calibration stay byte-identical. The user's own photos stay upright and give the same results. Index
build time grows by under 15%.

If an existing image turns, it is examined. A correct turn of a truly rotated photo would be a real
improvement, but it changes results, so the user decides. A wrong turn means raising the margin.

## Risks / Trade-offs

- **More false faces.** Four passes give more chances on an image with no face, as with the carved
  pumpkin. Measured on 597 non-face images, a new set, since the earlier images are no longer here.
- **LFW is tidy.** Real photos may have smaller gaps between orientations. The check on every image we
  have, including the phone photos, is the main protection, and the margin can be raised.
- **45 degrees stays poor.** It is stated in the proposal, and README's limits can say so.
- **A little more time per image,** on a small copy only.
