---
name: run-alterego-finder
description: Build, run, and drive AlterEgo Finder (calibrate.py, match.py). Use when asked to run the app, run match.py or calibrate.py, test the matching CLI end to end, or verify a change to the face-matching pipeline actually works.
---

AlterEgo Finder is a Windows Python CLI (no GUI, no server): `calibrate.py`
derives confidence thresholds from a held-out dataset, `match.py` ranks a
dataset's identities against a query photo. Drive it via
`.claude/skills/run-alterego-finder/driver.py`, which runs the real CLI
pipeline end to end against the repo's own `tests/fixtures/` — no dataset of
your own required. All paths below are relative to the repo root.

## Prerequisites

Windows, with Python 3.13 already on `PATH` (this box has it at
`C:\Users\proko\AppData\Local\Programs\Python\Python313\python.exe`, from a
`winget install OpenJS.NodeJS.LTS`-style install — for Python specifically it
was already present). No OS packages needed; `opencv-python` ships a
prebuilt Windows wheel.

If `python`/`pip` aren't on `PATH` in a fresh PowerShell, that's a new
install, not a config problem — install Python 3.13+ for Windows first.

## Setup

```powershell
python -m pip install -r requirements-dev.txt
```

This pulls in `requirements.txt` (`opencv-python`, `numpy`) plus `pytest`.
`numpy` is intentionally **not** pinned `<2` in `requirements.txt` — that pin
has no Python 3.13 Windows wheel and triggers a from-source build that needs
Visual C++ Build Tools. Don't reintroduce it.

No env vars, no build step, no model download — the DNN weights under
`models/` are vendored in the repo (see `models/README.md`).

## Run (agent path)

```powershell
python .claude\skills\run-alterego-finder\driver.py
```

(Same command works unmodified from Git Bash: `python .claude/skills/run-alterego-finder/driver.py`.)

The driver: runs `calibrate.py` against `tests/fixtures/calibration/` to get
real thresholds, runs `match.py` against `tests/fixtures/dataset/` with a
known query photo and asserts a `HIGH_CONFIDENCE` match on the right person,
then runs `match.py` against a synthesized blank image and asserts the
no-face error path (exit 1, exact message). All temp files go through
Python's own `tempfile.TemporaryDirectory()` — see Gotchas for why that
matters here. Prints `All driver checks passed.` and exits 0 on success;
raises `AssertionError` at the failing step otherwise.

Direct invocation (what the driver wraps, if you want to run one step by
hand):

```powershell
python calibrate.py --calibration-dir tests\fixtures\calibration --config-out C:\path\to\config.json
python match.py --image tests\fixtures\obama_query.jpg --dataset tests\fixtures\dataset --config C:\path\to\config.json
```

`match.py --help` / `calibrate.py --help` document all flags.

## Run (human path)

Same commands as above, against your own dataset:

```powershell
python match.py --image data\my_photo.jpg --dataset data\celebrities\ --config data\config.json
```

Requires `data/config.json` (from running `calibrate.py` against your own
`data/calibration/` first) or explicit `--threshold-low`/`--threshold-high`.

## Test

```powershell
python -m pytest tests/ -v
```

30 tests pass as of the `add-threshold-calibration` change.

---

## Gotchas

- **`cv2.imwrite()` silently fails (`ok == False`, no exception) when the
  destination path is a hand-typed POSIX-style string run through Git
  Bash's `python -c "..."`** — e.g. `cv2.imwrite('/tmp/x.jpg', img)`.
  Git Bash/MSYS auto-rewrites POSIX-looking *whole command-line arguments*
  to Windows paths (that's why `--config-out /tmp/config.json` on the CLI
  works fine), but it does **not** rewrite POSIX paths embedded *inside* a
  quoted Python string body — so the literal string `/tmp/x.jpg` reaches
  Windows, which resolves it to a nonexistent `C:\tmp\x.jpg`, and OpenCV
  just returns `False`. Fix: never hand-type `/tmp/...` inside inline
  Python; use `tempfile.TemporaryDirectory()` (as the driver does) or a
  real Windows path.
- **Output ordering can look scrambled when a subprocess writes to both
  stdout and stderr** (seen running the driver from PowerShell: the
  no-face step's stderr line printed *before* the calibrate.py section's
  stdout). This is display buffering, not a logic bug — check the actual
  return codes/assertions, not the interleaving order.

## Troubleshooting

- **`pip install` tries to compile numpy from source and fails with
  `Unknown compiler(s): [['icl'], ['cl'], ...]`**: you (or a dependency
  pin) reintroduced `numpy<2`, which has no Python 3.13 Windows wheel.
  Use `numpy>=1.24` (unpinned upper bound) as in `requirements.txt`.
- **`match.py` exits 1 with `Error: No calibrated thresholds available.`**:
  expected when neither `--config`/`data/config.json` nor both
  `--threshold-low`/`--threshold-high` are given — run `calibrate.py`
  first, or pass thresholds explicitly.
