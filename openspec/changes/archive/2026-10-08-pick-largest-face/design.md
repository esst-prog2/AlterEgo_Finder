## Context

See proposal.md - Why. `detect_face` in `face_pipeline/detector.py` runs
YuNet with `SCORE_THRESHOLD = 0.9` and returns `faces[0]`, the top-scoring
detection. Detection feeds both `match.py` (the query) and indexing
(`build_index`, calibration), so the rule applies everywhere.

## Goals / Non-Goals

**Goals:**
- The user's photo (sunglasses, turned head, printed face on the shirt)
  yields the user's own face.
- The selection rule lives in a pure function testable without the model.

**Non-Goals:**
- Telling real faces from printed ones in general (liveness detection).
- Letting the user choose a face when there are several.

## Decisions

1. **Cutoff 0.8.** The user's face scored 0.899; 0.8 leaves margin without
   admitting the low-score clutter seen on the same photo (next detection
   below the two faces scored 0.336). Alternative: 0.6, the value some
   YuNet examples use; rejected as a larger change than needed to unblock.
2. **Largest box area wins.** On the user's photo the real face's box is
   about 134x171 px against 40x54 px for the print, a clear gap, whereas the
   scores differ by 0.002. Alternative: keep top score; rejected, it is the
   bug. Alternative: score x area; rejected as harder to explain for no gain
   in the cases we have.
3. **Pure helper `pick_largest_face(faces)`** takes YuNet's raw (k, 15)
   output and returns the chosen row, so the rule has a planted-answer test
   that doesn't need the ONNX model.

## Risks / Trade-offs

- [A group photo where the intended person isn't the largest face] → out of
  scope; the README's demo is a single-subject query.
- [The lower cutoff admits more false detections] → those are small boxes in
  practice and lose to the real face under the largest-area rule.
- [Index caches keep old embeddings for unchanged multi-face images] →
  delete the dataset's `.matchcache/` after upgrading.
