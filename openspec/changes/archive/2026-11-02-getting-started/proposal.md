## Why

Nobody but the author can run AlterEgo Finder today. A fresh clone has no
dataset and no thresholds (`data/celebrities/`, `data/calibration/` and
`data/config.json` are gitignored), so the web UI stops at "No indexed dataset"
and the steps that built them exist only in PLANNING_LOG.md. The demo audience
scores whether they would use the program, and "what would it take for someone
to use it?" currently has no answer.

## What Changes

- **New `setup_data.py`**: one command takes a fresh clone to a working web UI:
  - downloads LFW to the user's machine, verified against a SHA-256 checksum;
  - builds `data/celebrities/` (500 faces) and `data/calibration/` (200 people)
    from a committed list of exact file paths;
  - runs the existing calibration, which writes `data/config.json` and indexes
    the dataset, so it appears in the page's dropdown.
- **New `data/lfw_split.json`**: the committed list. File paths only, never
  images. It records today's dataset, so anyone who runs setup gets the same
  faces and the scores in README section 1.
- Running it again is safe: finished steps are skipped, and it touches nothing
  outside those two folders, the download folder and `config.json`.
- **Web UI**: the "no indexed dataset" message now names `setup_data.py`.
- **README**: a "Getting started" section (install, setup, run, how long it
  takes and how much disk it needs), how to recreate Beat 2 with two photos of
  your own, and a troubleshooting note on Windows application control.

## Capabilities

### New Capabilities

- `project-setup`: one-command data setup: verified download, reproducible
  dataset, calibration, safe re-runs and clear failures.

### Modified Capabilities

- `web-ui`: "Dataset selection": with no indexed dataset, the page names the
  setup command as well as the CLI.

## Impact

- New: `setup_data.py`, `data/lfw_split.json`, `tests/test_setup_data.py`.
- Changed: `app.py` (one message), `README.md`, `AGENTS.md`, the
  run-alterego-finder skill.
- No new dependencies: standard library plus what `calibrate.py` already uses.
- LFW images are still never committed; the user's own photos are not involved.
- Network use: the one LFW download (about 180 MB), on top of the existing
  model-weight download. README section 5's privacy note says so. The query photo
  still never leaves the machine.
- The demo path (README section 1) does not change.
