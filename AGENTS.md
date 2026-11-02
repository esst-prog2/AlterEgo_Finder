# AGENTS.md

## Planning log

Whenever we decide something about this project — a requirement, a number,
a name, a tool — append one line to PLANNING_LOG.md: the date, what was
decided, and who's responsible for it:
- "Decided by user" — I originated the decision myself.
- "Proposed by agent, accepted by user" — you proposed it and I accepted it.
- "Decided by agent" — you decided it unilaterally (e.g. an implementation
  detail), without asking me first.

Never rewrite an earlier line.

## Project

AlterEgo Finder — a CLI tool that matches a query face photo against a dataset
of face images using face embeddings and vectorized cosine similarity, with a
calibrated confidence threshold. See [README.md](README.md) for the full
spec: demo walkthrough, scope (in/out), acceptance criteria, and risks.

## Status

MVP complete, matching README section 3's "First useful version" scope:
detection+alignment (YuNet), ArcFace (512-d) embedding, dataset
auto-indexing, calibrated two-threshold confidence classification
(`calibrate.py`), model weights fetched on demand with SHA-256
verification, and a self-contained `summary.html` report. 8 capabilities
under `openspec/specs/` (`web-ui`, `project-setup` and `public-figure-pool` added for
the final demo), all archived changes under
`openspec/changes/archive/`. See PLANNING_LOG.md for
the decision history.

HW5 (branch `hw5-usable`): `calibrate.py --dataset` fits `threshold_high`
to absent strangers' top-1 scores at the dataset's index size (HW4 spike),
and face detection uses the largest face with a 0.8 cutoff. Known open
issue: `match.py` prints every ranked candidate, not just the top few.

HW6 (branch `hw6-review`): four specialised reviews (security,
correctness, tests, docs/spec drift), one commit each; findings and what
was left open are in PLANNING_LOG.md. The two issues left open became
OpenSpec changes on branch `hw6-open-issues`: `limit-match-output`
(`match.py` prints the top 10 candidates, `--top N` for more) and
`config-path-follows-dataset` (specs name the config.json the code uses).
58 tests passing.

Final demo: README section 1 is a three-beat story in a local web UI
(`revise-demo-description`). Branch `streamlit-web-ui` builds it: `app.py`
(Streamlit, localhost only, see `.streamlit/config.toml`) on the pipeline in
`face_pipeline/matching.py`, which `match.py` now uses too; Streamlit is in
`requirements-ui.txt` only. Branch `similarity-target` adds the
similarity target (exact `1 - score` distances with threshold rings, layout in
`face_pipeline/target.py`; the chart's data stays inline because Windows'
application control blocks pyarrow here).

Branch `getting-started` adds `setup_data.py`: one command from a fresh clone
to a working page (verified LFW download, datasets built from the committed
`data/lfw_split.json`, calibration). README section 6 has the steps.

Branch `online-candidate-pool` adds an optional pool of 500 recognisable adults
(no politicians) in `data/wikidata`: built once by `setup_data.py --wikidata` from
the committed `data/wikidata_people.json`, rate limited and resumable, with photo
credits on cards and in the report, and its own thresholds (a dataset's
`config.json` wins over its parent's). `cv2.imread` fails silently on non-ASCII
paths on Windows, so dataset folder names stay ASCII. 208 tests passing (the 28 in
`tests/test_app.py` are skipped without Streamlit). Next: move Beat 1 onto the pool
in README section 1, before the 2026-11-07 hand-in.

## Workflow

This repo uses OpenSpec for spec-driven changes (openspec/):

- New work starts as a change proposal, not a direct edit — use
  `/opsx:propose "<idea>"`, or `/opsx:explore` to think it through first.
- Durable specs live under `openspec/specs/`; in-flight work under
  `openspec/changes/`.
- Don't hand-edit files under `openspec/changes/` — use the OpenSpec CLI
  (e.g. `openspec new change ...`) so required metadata stays consistent.
