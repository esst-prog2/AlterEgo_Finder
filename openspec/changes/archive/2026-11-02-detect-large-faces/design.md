## Context

`detect_face` runs YuNet once at the image's own size, with a score cutoff of 0.8, and
returns the largest face. On the two failing photos the score rises as the image shrinks.
`extract_embedding` aligns from the landmarks on the image it was given, so landmarks must
be in full-size coordinates. LFW images are 250 px; pool images are at most 909 px, and all
of them passed at full size.

## Goals / Non-Goals

**Goals:**
- Large phone photos with a clear face are detected.
- Images found at full size today give byte-identical results.

**Non-Goals:**
- Rotating images, or lowering the cutoff.
- Re-admitting the two pool people skipped as having no face (their places are filled).

## Decisions

### D1. Fallback only, full size first
Full size runs first and returns if it finds anything. *Alternatives rejected:*
- **Always shrink first:** every embedding would change, and with it LFW's thresholds and
  the README's scores.
- **Lower the cutoff:** the first photo would pass, but 0.58 for the second is about what
  false boxes score, and it would admit false faces everywhere.

### D2. Copies at 1600, 1024 and 640, largest first
Stop at the first size with a face, and use only sizes smaller than the image. Largest
first keeps the landmarks as precise as possible. Downscaling uses `INTER_AREA`. Copies are
never enlarged, so 250-px LFW images are never retried, which keeps calibration stable. The
largest-face rule applies within the size that succeeded.

### D3. Map back, then clip
The row's box and landmarks are divided by the scale, then pass through the existing box
clipping, so callers see only full-size coordinates and `align_face` is untouched.

### D4. Tests without private photos
The real photos are private and gitignored, so they are not fixtures. Task 1.1 looks for an
enlarged fixture face that fails at full size and passes on a copy. If none exists, the
retry logic is tested with a fake detector and the real photos are checked by hand only.

## Risks / Trade-offs

- [False faces on copies] -> checked on a carved pumpkin with the face cropped out and on a
  blank image (none found). Task 2.3 runs more non-face images and counts any faces found.
- [Slower on images with no face] -> at most three more passes, only for large images.
- [A wrong small face passes on a copy while the real large one is still missed] -> the
  result is then wrong rather than "No face detected". Rare and accepted.

## Migration Plan

Additive. A cached index stays valid for images that passed at full size. Rollback is
reverting the commit.
