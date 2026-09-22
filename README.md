# AlterEgo Finder

## 1. The demo

I open the terminal and run `python match.py --image data/my_photo.jpg --dataset data/celebrities/`. Within 100 ms, it extracts the face embedding, queries a pre-computed vector index matrix, and evaluates the results against thresholds calibrated for this dataset (run once via `calibrate.py`, not a fixed number baked into the code). It prints the top matching records alongside a categorical match quality (`HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, or `NO_MATCH`). I open `data/results/summary.html`, which renders my query image alongside the candidate matches, highlighting the top match's confidence level. If I pass an image file containing no detectable face (`data/blank.jpg`), the program exits with code 1, printing `Error: No face detected in input image`.

## 2. The shape

```
in            data/my_photo.jpg (an image file) + data/celebrities/ (a directory of target face images,
              indexed automatically on first run into a cached .npy vector matrix)
out           data/results/summary.html (visual match report with threshold status) +
              stdout top matches with categorized confidence
in between    detect + align face -> extract a fixed-length embedding vector ->
              vectorized matrix multiplication against the indexed embeddings ->
              apply match-confidence calibration rules -> render visual report
```


## 3. The size

### First useful version

- CLI tool taking a query image and a dataset directory, auto-indexed into a cached embedding matrix.
- Vectorized cosine similarity computation using matrix operations to handle scale efficiently (10,000+ pre-indexed vectors in under 50 ms).
- Match interpretation engine: calculating a confidence score and classifying each candidate as `HIGH_CONFIDENCE`, `LOW_CONFIDENCE`, or `NO_MATCH` using two thresholds — not chosen by hand, not hardcoded. Both come from the same calibration step: measuring the similarity distributions of same-person vs. different-person pairs in a held-out slice of the dataset, then picking the lower boundary at the equal-error-rate point and the upper boundary at a stricter operating point for the high-confidence claim.
- Automated generation of a self-contained `summary.html` report clearly indicating match validity.

### Not this term

- Real-time webcam stream matching.
- Automated web scraping or live downloads from external image APIs.
- Full web application / React frontend dashboard.
- Approximate Nearest Neighbor (ANN) index trees (e.g. FAISS / Annoy) — a vectorized matrix product over BLAS is sufficient at this term's dataset size; revisit if the dataset grows past what fits comfortably in memory.

## 4. How we would know it works

- Given an image with no recognizable face, the tool exits with status code 1 and prints `Error: No face detected in input image`.
- Given two different photos of Person A and one photo of Person B, the top-ranked match for Person A's query photo is Person A's other photo, with a higher similarity score than Person B's photo.
- Given a query face whose closest match in the dataset scores below the calibrated low threshold, the report explicitly flags the outcome as `NO_MATCH` rather than presenting a low-confidence candidate as a match.

## 5. What could stop this

- **Privacy & GDPR / legal risk:** storing or using sensitive real-world personal data without consent. Mitigation: the tool uses a publicly available, open-license dataset (LFW - Labeled Faces in the Wild), running entirely offline without uploading images anywhere.
- **Performance bottleneck at scale:** pre-computing face embeddings into a single consolidated `.npy` vector matrix during initialization, reducing matching to one vectorized matrix product (BLAS-optimized) instead of a per-file Python loop.
