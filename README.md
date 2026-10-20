# AlterEgo Finder

## 1. The demo

I run `streamlit run app.py` and open the page at `http://localhost:8501`; it is served on my machine only. The dataset dropdown lists the folders under `data/`, and `data/celebrities` (500 LFW faces, indexed once into a cached embedding matrix) is selected. The two thresholds sit on one range slider, preset to the values `calibrate.py` fitted for this dataset rather than numbers baked into the code. I drag `data/my_photo/PK.jpg` onto the page.

**Beat 1: my celebrity lookalike.** The page shows my photo, the face crop the model actually saw, and the ten closest celebrities as cards, each with its similarity score and a label: `HIGH_CONFIDENCE`, `LOW_CONFIDENCE` or `NO_MATCH`. The top card (Jean-Sebastien Giguere, 0.2146 in our run) is labelled `LOW_CONFIDENCE`: he looks somewhat like me, and the calibrated system knows he is not me.

**Beat 2: the system recognises the real person.** I switch the dropdown to `data/celebrities_plus_me`: the same 500 identities plus one more, `Me_PK`, holding a second photo of me taken on a different day and place (a local folder, kept out of the repository). Without uploading again, the page ranks `Me_PK` first at 0.4322, labelled `HIGH_CONFIDENCE`, about twice the best celebrity score. The threshold that kept every celebrity out of `HIGH_CONFIDENCE` lets the real person in. It is one self-match, at a threshold set so that about 1 in 100 people absent from the dataset would still reach it: evidence that the labels mean something, not proof of identity. A download button gives me the same result as a self-contained `summary.html` report.

**Beat 3: no face.** I drop an image with no face on it (a blank white image). Instead of cards, the page shows the error "No face detected".

The same pipeline is behind the CLI: `python match.py --image data/my_photo/PK.jpg --dataset data/celebrities/` prints the same top 10 in the terminal and writes `data/results/summary.html`, and on an image with no detectable face it exits with code 1, printing `Error: No face detected in input image`.

## 2. The shape

```
in            data/my_photo/PK.jpg (an image file) + data/celebrities/ (a directory of target face images,
              indexed automatically on first run into a cached .npy vector matrix), given through
              one of two front ends on the same pipeline: the local web page (app.py, localhost)
              or the CLI (match.py --image ... --dataset ...)
out           data/results/summary.html (visual match report with threshold status) +
              top matches with categorized confidence: result cards on the web page,
              or lines on stdout from the CLI
in between    detect + align face -> extract a fixed-length embedding vector ->
              vectorized matrix multiplication against the indexed embeddings ->
              apply match-confidence calibration rules -> render visual report
```


## 3. The size

### First useful version

- CLI tool taking a query image and a dataset directory, auto-indexed into a cached embedding matrix.
- Vectorized cosine similarity computation using matrix operations to handle scale efficiently (10,000+ pre-indexed vectors in under 50 ms).
- Match interpretation engine: calculating a confidence score and classifying each candidate as `HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, or `NO_MATCH` using two thresholds — not chosen by hand, not hardcoded. Both come from the same calibration step: measuring the similarity distributions of same-person vs. different-person pairs in a held-out slice of the dataset, then picking the lower boundary at the equal-error-rate point and the upper boundary at a stricter operating point for the high-confidence claim. The upper boundary must be fitted to the *top-1* score that people absent from the dataset get against an index of the dataset's actual size, not to pairwise scores. A 1% pairwise false-accept rate does not survive rank-1 search: on LFW, the pairwise 1% threshold labelled 33% of absent strangers `HIGH_CONFIDENCE` at 50 indexed faces, 99% at 500 and 100% at 5000 (`spike_eval.py`, `data/spike_results.json`, issue #4). The 1% point of the top-1 distribution is ~0.28 at 50 faces and ~0.44 at 5000. `calibrate.py --dataset <dir>` fits the upper boundary this way, using the calibration identities as absent strangers against that dataset's index (OpenSpec change `fit-high-threshold-to-index-size`); re-run it whenever the dataset grows.
- Automated generation of a self-contained `summary.html` report clearly indicating match validity.

### Final demo version

- Local web UI (Streamlit, `app.py`) over the same pipeline as the CLI, served on localhost only: drag-and-drop photo upload, a dataset dropdown over the folders under `data/`, one range slider for the two thresholds (preset to the calibrated values, so the low boundary cannot be dragged above the high one), the query's aligned face crop, the top 10 candidates as cards with score and label, and the `summary.html` report previewed and downloadable. The CLI keeps working as before.

### Not this term

- Real-time webcam stream matching.
- Automated web scraping or live downloads from external image APIs.
- Hosted, multi-user web application (public URL, accounts) / React frontend dashboard; the web UI runs on the user's own machine only.
- Approximate Nearest Neighbor (ANN) index trees (e.g. FAISS / Annoy) — a vectorized matrix product over BLAS is sufficient at this term's dataset size; revisit if the dataset grows past what fits comfortably in memory.

## 4. How we would know it works

- Given an image with no recognizable face, the tool exits with status code 1 and prints `Error: No face detected in input image`.
- Given two different photos of Person A and one photo of Person B, the top-ranked match for Person A's query photo is Person A's other photo, with a higher similarity score than Person B's photo.
- Given a query face whose closest match in the dataset scores below the calibrated low threshold, the report explicitly flags the outcome as `NO_MATCH` rather than presenting a low-confidence candidate as a match.
- Given the same photo, dataset and thresholds, the web UI shows the same top 10 candidates, scores and labels, in the same order, as `match.py` prints.
- Given an image with no detectable face, the web UI shows "No face detected" and no candidates or report.
- While the web UI runs, it listens on `127.0.0.1:8501` only (not reachable from other devices), with Streamlit's usage statistics turned off.

To run the web UI: `pip install -r requirements-ui.txt`, then `streamlit run app.py` from the repository root.

## 5. What could stop this

- **Privacy & GDPR / legal risk:** storing or using sensitive real-world personal data without consent. Mitigation: the tool uses a publicly available, open-license dataset (LFW - Labeled Faces in the Wild), running entirely offline without uploading images anywhere (the only network access is the one-time, checksum-verified download of the two model weight files). The web UI is served on localhost only, so the photo dropped onto the page is processed on this machine and is neither sent anywhere nor reachable from other devices on the network. The second photo of me used in the self-match demo is my own and stays out of the repository.
- **Performance bottleneck at scale:** pre-computing face embeddings into a single consolidated `.npy` vector matrix during initialization, reducing matching to one vectorized matrix product (BLAS-optimized) instead of a per-file Python loop.
