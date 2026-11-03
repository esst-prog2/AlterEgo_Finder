## Why

The pool holds one photo per person, so a poor photo can hide someone: Bruce Springsteen's
LFW photos miss his pool photo. Enrolling several photos per person might fix that, but it
may also raise the thresholds and take the gain back, and a full build means 2 hours or more
of downloads, per-person ranking and a new look at the target. We also discussed walking
outward from lookalike to lookalike online. A small offline measurement answers both before
anything is built, as the HW4 spike did for thresholds.

## What Changes

- **A throwaway spike script, `spike_multiphoto.py`,** like `spike_eval.py`, with results in
  `data/spike_multiphoto_results.json`. It answers:
  1. On about 50 people with up to 4 photos each, how do **one photo, best photo, averaged**
     and **extra photos for the top 10 only** compare on same-person matches, strangers
     reaching *Same person*, and `PK.jpg`'s own results?
  2. How well does a **simulated lookalike-to-lookalike walk** do, with LFW standing in for
     the web? How close does it get to the true best match, how many faces does it check,
     and how often does a walk lead back to the person's own face?
- **Photos in a gitignored `data/spike_multiphoto/`,** fetched once from Wikimedia Commons
  under the pool's rate limit and licence rules. No query photo is involved in any request,
  and the walk uses no network at all.
- **A decision rule fixed before the run,** so the result decides the next step.

Not changing: the program, the page, the pool, the thresholds and README's demo. No online
search is built.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: a measurement changes no requirement. This change declares `skip_specs`. If the result
justifies a full build, that is its own change with its own specs.

## Impact

- New: `spike_multiphoto.py`, `tests/test_spike_multiphoto.py`, the results file, and one
  `.gitignore` line. No new dependencies.
- About 30 minutes of considerate requests to Wikimedia, and about 25 minutes of local
  embedding. Resumable.
