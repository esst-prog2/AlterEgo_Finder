# AlterEgo Finder

## 1. The demo

I run `streamlit run app.py`, open `http://localhost:8501`, pick the `wikidata` dataset (500 well-known people, one licensed Wikimedia Commons photo each) and drop `data/my_photo/PK.jpg` on the page, which never leaves my machine. The page shows the ten closest public figures as cards with scores and plain labels, next to a similarity target with me at the centre and every face at a distance of exactly one minus its score. The top card is Psy at 0.2702, labelled *Alter Ego*, and nobody reaches the inner *Same person* ring at 0.3706. I switch the dropdown to `wikidata_plus_me`, which adds a second photo of me from another day, and `Me_PK` jumps to first at 0.4322, labelled *Same person*, the one face inside that ring. It is one self-match, at a threshold about 1 in 100 people absent from the dataset would still reach: evidence that the labels mean something, not proof of identity. Finally I drop `data/demo/no_face.jpg`, and the page shows "No face detected" instead of cards.

## 2. The shape

```
in            data/my_photo/PK.jpg (an image file) + data/wikidata/ (a directory of target face images,
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

- Local web UI (Streamlit, `app.py`) over the same pipeline as the CLI, served on localhost only: drag-and-drop photo upload, a dataset dropdown over the folders under `data/`, one range slider for the two thresholds (preset to the calibrated values, so the low boundary cannot be dragged above the high one), the query's aligned face crop, the top 10 candidates as cards with score and label, a similarity target (each face at exactly one minus its score from the query, with the two threshold rings; direction means nothing), and the `summary.html` report previewed and downloadable. The CLI keeps working as before.

### Not this term

- Real-time webcam stream matching.
- Web scraping, reverse image search, or any download at match time. (The optional public-figure pool in section 6 is fetched once, ahead of time, from Wikimedia, and matching against it uses no network.)
- Hosted, multi-user web application (public URL, accounts) / React frontend dashboard; the web UI runs on the user's own machine only.
- Approximate Nearest Neighbor (ANN) index trees (e.g. FAISS / Annoy) — a vectorized matrix product over BLAS is sufficient at this term's dataset size; revisit if the dataset grows past what fits comfortably in memory.

## 4. How we would know it works

- Given an image with no recognizable face, the tool exits with status code 1 and prints `Error: No face detected in input image`.
- Given two different photos of Person A and one photo of Person B, the top-ranked match for Person A's query photo is Person A's other photo, with a higher similarity score than Person B's photo.
- Given a query face whose closest match in the dataset scores below the calibrated low threshold, the report explicitly flags the outcome as `NO_MATCH` rather than presenting a low-confidence candidate as a match.
- Given the same photo, dataset and thresholds, the web UI shows the same top 10 candidates and scores, in the same order, as `match.py` prints, with each label as its plain-language name (*Same person* for `HIGH_CONFIDENCE`, *Alter Ego* for `LOW_CONFIDENCE`, *Not You* for `NO_MATCH`); the technical names do not appear on the page.
- Given an image with no detectable face, the web UI shows "No face detected" and no candidates or report.
- Given a match, the web UI's similarity target places every indexed face at exactly one minus its similarity score from the centre, with rings at one minus each threshold that move with the slider, so the faces inside the inner ring are exactly the `HIGH_CONFIDENCE` ones.
- While the web UI runs, it listens on `127.0.0.1:8501` only (not reachable from other devices), with Streamlit's usage statistics turned off.

To run it yourself, see section 6.

## 5. What could stop this

- **Privacy & GDPR / legal risk:** storing or using sensitive real-world personal data without consent. Mitigation: the tool uses a publicly available, open-license dataset (LFW - Labeled Faces in the Wild), running entirely offline without uploading images anywhere (the only network access is the one-time, checksum-verified download of the two model weight files and, in `setup_data.py`, of LFW itself and, if asked for, of the pool's photos; LFW's images are downloaded from the source and never stored in this repository). The web UI is served on localhost only, so the photo dropped onto the page is processed on this machine and is neither sent anywhere nor reachable from other devices on the network. The second photo of me used in the self-match demo is my own and stays out of the repository. The optional public-figure pool adds real people's faces, and face embeddings are sensitive data, so it is limited to adults known to the public (no politicians), its photos and embeddings stay on the user's machine and are never committed, every photo's author and licence are recorded and shown wherever it appears, and building it never involves a query photo. This is a course project's position, not legal advice.
- **Performance bottleneck at scale:** pre-computing face embeddings into a single consolidated `.npy` vector matrix during initialization, reducing matching to one vectorized matrix product (BLAS-optimized) instead of a per-file Python loop.

## 6. Getting started

You need Python 3.10 or newer (tested on 3.13) and about 750 MB of free disk space. From a clone of this repository:

```
python -m venv .venv
.venv\Scripts\activate            (on macOS or Linux: source .venv/bin/activate)
pip install -r requirements-ui.txt
python setup_data.py
streamlit run app.py
```

Then open `http://localhost:8501` and drop a photo with a face on the page. `data/my_photo/PK.jpg` is there to try: its top match should be Jean-Sebastien Giguere at 0.2146.

`setup_data.py` downloads LFW (about 180 MB, checksum-verified), builds `data/celebrities` (500 faces) and `data/calibration` (200 people) from the file list in `data/lfw_split.json`, and calibrates the thresholds. Installing took about a minute and setup about 3.5 minutes on a home connection, most of it the download and calibration. Running it again is safe: it skips what is finished and leaves your other folders alone. Use `--tarball <file>` if you already have `lfw.tgz`, and `--recalibrate` to compute the thresholds again.

For the CLI alone, `pip install -r requirements.txt` is enough, and `python match.py --image <photo> --dataset data/celebrities` prints the matches.

**Optional: a pool of people you will recognise, used by the demo in section 1.** `python setup_data.py --wikidata` also builds `data/wikidata`: 500 well-known actors, footballers, singers, tennis players and racing drivers, one licensed photo each, chosen from the list in `data/wikidata_people.json`. It takes about 30 minutes, because it waits between requests to Wikimedia, and uses about 42 MB; stop it any time and run it again to continue. It then appears in the page's dropdown with its own thresholds, and works offline from then on. Use `--wikidata-limit 100` for a quicker, smaller pool. The thresholds are fitted with LFW faces as the strangers, while the pool's photos come from Wikimedia Commons, so read its confidence labels as a little less exact than LFW's. On the pool, `data/my_photo/PK.jpg`'s top match in our run was Psy at 0.2702.

**See your own self-match.** You need the pool above and two different photos of yourself. Copy `data/wikidata` to `data/wikidata_plus_me`, add one photo as `data/wikidata_plus_me/Me/me.jpg`, and index it once with `python match.py --image <your other photo> --dataset data/wikidata_plus_me` (about a minute and a half). The copy keeps the pool's thresholds and credits. The new dataset then appears in the page's dropdown; drop your other photo on the page. Without the pool, the same steps work from `data/celebrities`. Your photos stay on your machine, but check that they stay out of git too: `data/wikidata_plus_me/` is already in `.gitignore`, and any other folder name needs adding.

**Windows: "DLL load failed" or "an application control policy has blocked this file".** Smart App Control or a managed PC's policy is blocking a library. This project's page avoids the library known to be blocked (`pyarrow`, used by Streamlit for tables and DataFrame charts), so the program itself should not hit it. If another library is blocked, the fix is the policy's owner: do not turn off a security feature just for this project.
