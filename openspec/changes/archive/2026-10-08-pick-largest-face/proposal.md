## Why

The first real use of `match.py` (HW5 step 6, PLANNING_LOG.md 2026-10-08)
failed on an ordinary photo: the user, in sunglasses with the head slightly
turned, scored 0.899 at the face detector, just under its 0.9 cutoff, so
the CLI reported "No face detected". The same photo also has a second face,
printed on the user's T-shirt, scoring 0.897, so the current rule (take the
top-scoring face) would pick between the real face and the print on a 0.002
margin once the cutoff is lowered.

## What Changes

- The face detector's confidence cutoff drops from 0.9 to 0.8, so faces
  partly covered by sunglasses or slightly turned are still found.
- When an image contains several faces, the largest one (by bounding-box
  area) is used, not the one with the highest detector score. In a query
  photo the subject is normally the largest face; prints, posters and
  people in the background are smaller.

## Capabilities

### New Capabilities

### Modified Capabilities
- `face-embedding`: the face-detection requirement states which face is used
  when an image contains more than one.

## Impact

- `face_pipeline/detector.py`: cutoff constant and face-selection rule.
- Existing dataset index caches (`.matchcache/`) stay valid only for images
  with one face; they are rebuilt automatically when files change, but an
  unchanged multi-face image keeps its old embedding until the cache is
  cleared.
- New test fixture: the user's photo (data/my_photo/PK.jpg), committed with
  the user's consent.
