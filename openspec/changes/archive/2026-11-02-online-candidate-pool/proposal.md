## Why

Beat 1's lookalike today is "Jean-Sebastien Giguere". LFW is full of names nobody
in the room knows, and the audience scores whether they get the program and would
use it. A candidate pool chosen by fame turns the result into someone people
recognise. It is also the course's "real or bigger data" idea: real numbers, with
the licences and personal-data questions that come with them. A read-only spike
(PLANNING_LOG.md, 2026-11-02) showed it is feasible: 30 of 30 sampled images had a
detectable face and a usable licence, and the same person scored 0.46-0.57 across a
Wikidata and an LFW photo, above the high threshold.

## What Changes

- **New committed list `data/wikidata_people.json`**: adults with English names and
  at least 40 sitelinks, across actors, footballers, singers, tennis players and
  racing drivers, and no politicians, so a lookalike is never a political statement
  (identifiers, names and file names; no images), plus
  `refresh_wikidata_list.py`, which regenerates it.
- **`setup_data.py --wikidata`** (optional; `--wikidata-limit N`, default 500): builds
  `data/wikidata/` once, one image per person, waiting between requests and honouring
  rate limits, and resumable. Only images with a face, an author and an allowed
  licence are kept. It records `attribution.json` and calibrates the pool.
- **Per-dataset thresholds**: a dataset's own `config.json` takes precedence over the
  one in its parent folder, in the CLI and the web UI.
- **Calibration** leaves out calibration people who are also in the dataset when
  fitting the high threshold. LFW's thresholds do not change.
- **Attribution** (author, licence, source link) on result cards, tooltips and in
  `summary.html`, shown as plain text.
- **README**: sections 3, 5 and 6 cover the pool: built once from Wikimedia, never at
  match time, and the query photo is never sent anywhere. Real public figures' faces
  are processed locally, and the privacy note says so.

**Not in this change:** README section 1. Moving Beat 1 onto the pool changes its
names and scores, so it is a follow-up change once the numbers are measured, before
the hand-in on 2026-11-07. If the pool is not ready, the demo stays on LFW.

## Capabilities

### New Capabilities

- `public-figure-pool`: the committed selection, the considerate build, licence and
  face filtering, recorded attribution and the pool's own thresholds.

### Modified Capabilities

- `face-matching-cli`: "Threshold configuration" prefers a dataset's own `config.json`.
- `threshold-calibration`: "Threshold derivation" excludes calibration identities
  that are in the dataset.
- `summary-report`: new "Photo attribution in the report".
- `web-ui`: new "Photo attribution on the page".

## Impact

- New: `face_pipeline/wikidata_pool.py`, `face_pipeline/attribution.py`,
  `refresh_wikidata_list.py`, `data/wikidata_people.json`, tests.
- Changed: `setup_data.py`, `calibrate.py`, `match.py`, `app.py`,
  `face_pipeline/matching.py`, `face_pipeline/report.py`, `.gitignore`, README.
- Network: Wikimedia, only during the optional build. No new dependencies.
- Personal data: public figures' photos and embeddings on the user's machine, never
  committed. Reverse image search stays out of scope.
- Time: about 25 minutes to build 500 images at one request per 3 seconds.
