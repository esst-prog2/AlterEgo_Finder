## Context

`data/celebrities/` (500 identities, one image each) and `data/calibration/`
(200 identities, up to 4 images each) were built by hand on 2026-10-08 from
`spike_eval.py`'s seed-0 split. That split selects faces by running detection
and skipping images with no face, and the detector's cutoff has changed since
(`pick-largest-face`). `spike_eval.py` is throwaway code that also runs the whole
experiment. `calibrate.py --calibration-dir ... --dataset ...` already embeds,
fits both thresholds, indexes the dataset and writes `config.json` (about 3
minutes on this machine). The HW6 security review noted that `urlretrieve` has
no timeout, and `face_pipeline/weights.py` already has the `.part` + SHA-256
pattern for downloads.

## Goals / Non-Goals

**Goals:**
- A newcomer gets the same dataset, thresholds and README scores with one command.
- The script needs nothing beyond the CLI's dependencies.

**Non-Goals:**
- Choosing another dataset or size (`calibrate.py` and `match.py` already take
  any folder).
- An installer, a packaged `.exe` or Docker. An unsigned `.exe` is exactly what
  Windows application control blocks.
- Automating Beat 2's self-match dataset. It needs the user's own photos, so the
  README explains it.
- Replacing `spike_eval.py`, which stays as the record of the HW4 experiment.

## Decisions

### D1. A committed list of exact paths, not re-running the split
`data/lfw_split.json` holds `{"celebrities": [...], "calibration": [...]}` with
archive-relative paths such as `Aaron_Sorkin/Aaron_Sorkin_0001.jpg`. It is
generated once from today's folders. *Alternative rejected:* re-running the
seeded split at setup time. It would need detection on about 700 images, and
with today's cutoff it could pick different faces, so README's 0.2146 would no
longer reproduce. The list records one fixed dataset, and names and file names
are already public in LFW.

### D2. Extract only the listed files, by name from our list
The script walks the archive once as a stream (`tarfile` mode `r|gz`) and writes
only the members named `lfw/<listed path>`, rather than extracting everything.
Looking members up by name is far too slow on a `.tgz`: a first attempt ran over
5 minutes, while one sequential pass over all 13,000 files takes under 3 seconds.
Streaming also avoids writing about
13,000 unused files (the extracted archive is hundreds of MB) and rules out
path traversal, because output paths come from the committed list, not from
archive contents. Each file is written to a temporary name and renamed, so an
interrupted run leaves no half-written image. Existing files of the right size
are skipped.

### D3. Download like `weights.py`
Download to `data/lfw/lfw.tgz.part` with a socket timeout, verify SHA-256, then
rename to `lfw.tgz`. `urllib` with a timeout, so a stall fails instead of hanging.
Progress is printed every 10%, since this is the slowest silent step. The URL and
checksum are `spike_eval.py`'s: the figshare mirror scikit-learn uses, and
scikit-learn's published SHA-256. `--tarball PATH` uses an existing archive,
verified the same way, which is also how tests and offline runs avoid the network.

### D4. Reuse `calibrate.main`
Calibration calls `calibrate.main(["--calibration-dir", ..., "--dataset", ...])`,
so setup and the documented CLI cannot drift apart. It is skipped when
`config.json` and the index both exist, unless `--recalibrate` is passed. If only
the index is missing, `get_or_build_index` builds it.

### D5. `setup_data.py` at the repository root, with a `--data-dir` option
It sits next to `match.py` and `calibrate.py`. The name avoids `setup.py`, which
Python tools treat as a packaging script. `--data-dir` (default `data/`) lets
tests use a temporary folder.

### D6. Testing
`tests/test_setup_data.py` builds a tiny archive from fixture images plus a small
split list, and passes them in, so no network and no LFW are needed:
- files land where the list says, byte-identical to the archive;
- a wrong checksum exits non-zero and builds nothing;
- a listed image missing from the archive exits non-zero and names it;
- a second run does not recalibrate (config unchanged);
- a run after an interruption finishes the job;
- other folders under `data/` are untouched;
- the real `data/lfw_split.json` has 500 + 200 disjoint identities, one image per
  candidate, at most 4 per calibration identity.

The real proof is end to end in a **fresh clone** (task 4.1), driven in Chromium
and compared with README's scores.

## Risks / Trade-offs

- [The figshare mirror goes away] → a clear error, and `--tarball` accepts a copy
  from elsewhere; the checksum still protects it.
- [LFW's licence terms] → the images are downloaded by the user from the source
  and never redistributed in this repository; README says so.
- [A different machine gives slightly different thresholds or scores] → ArcFace
  INT8 on OpenCV should be deterministic for the same files, but floating-point
  results could vary in the last digits across CPUs. The fresh-clone check runs on
  this machine only; README's scores are stated as "in our run".
- [Windows application control blocks something on a newcomer's PC] → the README
  note explains the error and that the app avoids pyarrow at runtime.
- [Setup takes minutes] → the README states the time, and each step prints what
  it is doing.

## Migration Plan

Additive. An existing checkout with data keeps it: setup sees the files and config
and does nothing. Rollback is deleting the script and list.
