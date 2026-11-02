## 1. Tests first

- [x] 1.1 Search for a committable test image: an enlarged fixture face that the current detector misses at full size and finds on a copy. Record the result. If none exists, use a fake detector for the retry logic
- [x] 1.2 Write tests in `tests/test_detector.py`: a face missed at full size is found (box and landmarks in full-size coordinates, inside the image); sizes are tried largest first, only below the image's size, stopping at the first hit; found at full size means no retry; a large blank image gives None; a small image is never retried. See them fail

## 2. The fix

- [x] 2.1 Implement the fallback in `face_pipeline/detector.py` (design D1-D3); verify the new and existing tests pass
- [x] 2.2 Mutation-check: always retrying, and not mapping landmarks back, must each fail a test
- [x] 2.3 Verify nothing else moved: `calibrate.py` to a scratch file is byte-identical to `data/config.json`, rebuilt embeddings for `data/celebrities` and `data/wikidata` match their caches, and `PK.jpg` still gives Psy 0.2702 and Giguere 0.2146. Run the detector over non-face crops of `photo_face_problem` and `data/demo/no_face.jpg`, and report any faces found

## 3. Proof and record

- [x] 3.1 In Chromium, drop both photos from `photo_face_problem` on the page: cards appear, and the face crop shows the actual face. Walk through README's three beats
- [x] 3.2 Update AGENTS.md and the skill's test counts; verify `pytest` in full, and with Streamlit hidden; append the outcome to PLANNING_LOG.md
