## Why

README section 1 (revised by `revise-demo-description`) now walks the final
demo through a local web page: drop a photo, see the top 10 as cards, switch
the dataset to show the self-match, drop a no-face image. The audience judges
whether they would use the program; a browser page they can picture using
carries that better than terminal lines. The page does not exist yet.

## What Changes

- **New local web UI** (`app.py`, Streamlit), served on localhost only:
  - drag-and-drop upload of a JPEG/PNG query photo;
  - a dataset dropdown listing the folders under `data/` that already have
    an embedding index;
  - one range slider for the two thresholds, preset to the calibrated values
    from `config.json`, with a note whenever they differ from those values;
  - a "candidates shown" control (1-20, default 10);
  - the query's aligned face crop, and the top candidates as cards with
    person, image, score and label;
  - the self-contained `summary.html` report, previewed on the page and
    downloadable;
  - the error "No face detected" (and no cards or report) for an image with
    no detectable face;
  - switching dataset or moving a slider re-runs the match on the photo
    already uploaded.
- **Refactor, no behavior change**: the matching steps inside `match.py`'s
  `main()` (load thresholds, embed the query, rank, classify) move to a
  shared module, `face_pipeline/matching.py`, with a `match_image()` entry
  point used by both the CLI and the UI. `match.py` keeps its options,
  output and exit codes, and still exposes `classify` (two tests import it).
- `render_report()` also accepts the query as an image array, so the UI never
  writes the uploaded photo to disk except inside the report (as the CLI
  already does).
- **Configuration**: `.streamlit/config.toml` binds the server to
  `localhost` and turns off Streamlit's usage statistics, so the page sends
  nothing off the machine; `requirements-ui.txt` adds Streamlit on top of
  `requirements.txt`, keeping the CLI and its tests free of it.
- A committed no-face demo image, `data/demo/no_face.jpg`, for Beat 3.

## Capabilities

### New Capabilities

- `web-ui`: the local browser front end: serving only on localhost, upload,
  dataset selection, threshold and candidate-count controls, result cards,
  no-face and unreadable-image errors, and report preview/download.

### Modified Capabilities

None. `face-matching-cli` keeps all of its requirements (the refactor is an
implementation detail, pinned by the existing tests), and `summary-report`'s
requirements say "given a query image" without fixing how it is passed.

## Impact

- New: `app.py`, `face_pipeline/matching.py`, `.streamlit/config.toml`,
  `requirements-ui.txt`, `data/demo/no_face.jpg`, tests for `matching.py`
  and for the app.
- Changed: `match.py` (calls `face_pipeline/matching.py`),
  `face_pipeline/report.py` (`render_report` accepts an array as well as a
  path).
- New dependency, UI only: `streamlit`. Tests that need it are skipped when it
  is not installed, so `pip install -r requirements-dev.txt` plus `pytest`
  keeps working as before.
- The existing 60 tests run unchanged and must still pass.
- README: section 4 gains the UI's acceptance criteria and a "how to run the
  web UI" line (section 1-3 and 5 already describe it).
