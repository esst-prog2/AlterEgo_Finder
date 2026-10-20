## Context

All matching logic sits in `match.py`'s `main()`, mixed with argparse and
`print`: `_load_thresholds(args, dataset_path)`, `cv2.imread`,
`extract_embedding`, `get_or_build_index`, `rank_matches`, `classify`,
`render_report(image_path, ...)`. Two tests import `classify` from `match`.
`extract_embedding` detects, aligns and embeds in one call and keeps the
aligned crop to itself. `render_report` takes the query as a file path and
reads it with `cv2.imread`. YuNet and ArcFace are loaded once per process into
module globals. Under `data/`, only `celebrities/` and `celebrities_plus_me/`
have a `.matchcache/` index; `lfw/` (about 13k images), `calibration/`,
`results/`, `my_photo/` and `my_photo_test/` do not. Both indexed datasets
read `data/config.json` (low 0.1864, high 0.3643).

Streamlit re-executes the whole script on every widget change, so whatever is
slow must be cached or kept off the rerun path.

## Goals / Non-Goals

**Goals:**
- One matching code path for CLI and UI, so their results agree by
  construction.
- Moving a slider or switching dataset feels instant once the index is
  cached.
- The existing 60 tests run unchanged.

**Non-Goals:**
- Indexing new datasets from the page (the CLI does that).
- Uploading several photos at once, or a webcam.
- Concurrent multi-user use (one person, one machine).
- Calibrating from the page.

## Decisions

### D1. `face_pipeline/matching.py` holds the pipeline; the CLI and app are thin
- `load_thresholds(config_path) -> (low | None, high | None)`: the file part
  of today's `_load_thresholds`. The CLI keeps its `--threshold-*` overrides
  on top.
- `classify` and the three label constants move here. `match.py` re-imports
  them, so `from match import classify` still works.
- `QueryFace(embedding, aligned_face)` and `embed_query(image) -> QueryFace`.
  It raises `NoFaceDetectedError` like `extract_embedding`.
- `label_results(ranked, low, high) -> [(entry, score, label)]`.
- `match_image(image, index, low, high) -> MatchResult(query, labeled)`
  composes them. The CLI calls it. The app calls `embed_query` and
  `label_results` separately, so it can cache the embedding (D2).

To expose the crop without duplicating detection, `embedder.py` gains
`detect_and_align(image) -> aligned` (raises `NoFaceDetectedError`), and
`extract_embedding` becomes `embed_face(detect_and_align(image))`.

*Alternative rejected:* the app imports `match.py` and calls its helpers.
That would tie the UI to a CLI script built around argparse and stdout, and
`main()` returns an exit code, not results.

### D2. What each rerun recomputes
```
upload bytes --> embed_query      cached: st.cache_data, keyed on the bytes
dataset      --> get_or_build_index  called every rerun: a fresh cache costs one
                                     stat per file plus np.load (milliseconds)
             --> rank_matches     every rerun (one matrix product)
sliders      --> label_results    every rerun (instant)
             --> render_report    every rerun (10 image encodes)
```
Calling `get_or_build_index` on every rerun keeps the CLI's freshness rule
(a changed dataset is rebuilt, not served stale). `st.cache_resource` on the
index would skip that check. A rebuild, which is rare for a listed dataset,
runs under a spinner.

### D3. Datasets listed = folders directly under `data/` that have `.matchcache/embeddings.npy`
This lists exactly `celebrities` and `celebrities_plus_me` today. One wrong
pick of `lfw/` would otherwise start an index build of roughly 40 minutes
inside the page. *Alternative rejected:* every folder with person
subfolders, because `lfw/` and `calibration/` qualify. A new dataset appears
after one `match.py` run against it. Thresholds come from
`<dataset parent>/config.json`, as in the CLI. The UI has no `--config`
equivalent; the slider is the override.

### D4. Threshold range slider
One `st.slider` with a `(low, high)` tuple value. Streamlit's range slider
cannot cross its handles, which satisfies "low cannot be above high" without
a check of our own. Step 0.0001 and format `%.4f` are needed to preset 0.1864
and 0.3643 exactly. Bounds are `[min(0, low), max(1, high)]`, so test configs
with -1 still fit. The widget key includes the dataset name, so switching
dataset resets the slider to that dataset's calibrated values. The override
notice compares the values rounded to 4 decimals.

### D5. `render_report` accepts `Path | np.ndarray`; the UI writes `data/results/summary.html`
A path is read as today; an array is used directly. The decoded upload goes
straight in, and the photo is never saved as a separate file. The report is
written where the CLI writes it (gitignored `data/results/`). It is then read
back for `st.download_button` and previewed with `st.components.v1.html` in a
scrolling iframe. The `summary-report` spec doesn't change, because it never
fixes how the image is passed.

### D6. Upload handling
`st.file_uploader(type=["jpg", "jpeg", "png"])`, decoded with `cv2.imdecode`.
`None` means "Unable to read image file". `server.maxUploadSize = 10` (MB).
Person names are dataset folder names, which are untrusted (HW6 review 1), so
cards render them with `st.text` or `st.caption`, never with
`unsafe_allow_html`.

### D7. `.streamlit/config.toml`
```
[server]
address = "localhost"
maxUploadSize = 10

[browser]
gatherUsageStats = false
```
Streamlit binds to all interfaces by default and collects usage statistics
by default. Both would contradict README section 5. The file is read from the
working directory, so the run instruction is "from the repository root".

### D8. Dependencies and test isolation
`requirements-ui.txt` is `-r requirements.txt` plus `streamlit>=1.40,<2`.
App tests start with `pytest.importorskip("streamlit")`, so a CLI-only setup
still runs the whole suite (app tests skipped). `requirements-dev.txt` is
unchanged.

### D9. Testing the app
- `matching.py` is tested directly with pytest, red first, as in earlier
  changes.
- Page behavior is tested with `streamlit.testing.v1.AppTest`, headless.
  Older AppTest versions cannot drive `file_uploader`. So app.py puts
  everything after the upload in `show_results(image_bytes, dataset_dir,
  low, high, top)`, and upload-dependent scenarios (cards, no face,
  unreadable file, report) run it through `AppTest.from_function` with
  fixture bytes. If the installed version can drive `file_uploader`, those
  tests use the real uploader instead. Task 1.1 checks which applies.
- "Labels match the CLI" is tested by running both paths on
  `tests/fixtures/dataset` and comparing.

### D10. Demo no-face image
`data/demo/no_face.jpg` is a 300x300 white JPEG, the same image the no-face
tests generate. It's committed so Beat 3 has a file to drop. It has no index,
so it never appears in the dataset dropdown.

## Risks / Trade-offs

- [AppTest cannot drive the uploader] → D9's `show_results` seam. The real
  uploader is still covered by the manual three-beat run (task 4.1).
- [A listed dataset's cache goes stale and the page rebuilds for minutes] →
  spinner; it only happens if the dataset changes.
- [First match downloads model weights (network)] → the README already states
  this one-time, checksum-verified download. The spinner covers it.
- [Model globals shared across Streamlit sessions; `cv2.dnn` is not
  guaranteed thread-safe] → acceptable for one local user (Non-Goals). Revisit
  only if the UI is ever hosted.
- [`data/celebrities_plus_me` uses thresholds fitted to 500 faces at 501] →
  as in the logged self-match test; the difference is one face.
- [The report on disk contains the uploaded photo] → same as the CLI; it stays
  in gitignored `data/results/` on this machine.
- [Streamlit changes behavior in a minor release] → version range in
  `requirements-ui.txt`.

## Migration Plan

Additive. `match.py` keeps its interface. Rollback is reverting the change's
commits; the CLI keeps working on its own throughout.
