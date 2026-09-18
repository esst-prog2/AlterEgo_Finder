# AlterEgo Finder

## 1. The demo

I open the terminal and run `python match.py --image data/my_photo.jpg --dataset data/celebrities/`. Within 300 ms, it processes the face embedding and prints the top three closest matching records with their similarity confidence scores. I open the generated output directory `data/results/`, which contains an HTML report (`summary.html`) rendering my input photo alongside the top three matched faces and their names. If I pass an image file containing no detectable face (`data/blank.jpg`), the program exits with code 1, printing `Error: No face detected in input image`.

## 2. The shape

```
in            data/my_photo.jpg (an image file) + data/celebrities/ (a directory of target face images)
out           data/results/summary.html (visual match report) + stdout top-3 matches with similarity percentages
in between    detect face bounding box -> compute 128-dimensional face embedding vector ->
              calculate cosine similarity against pre-indexed dataset vectors -> rank and generate report
```


## 3. The size

### First useful version

- CLI tool accepting a single input image (.jpg/.png) and a local target image directory.
- Face detection and 128-d vector embedding extraction using an open-source model (e.g., dlib / insightface / facenet).
- Cosine similarity matching against pre-computed embeddings of the dataset.
- Generating a lightweight standalone `summary.html` file showing the query face side-by-side with the top matches and similarity scores.

### Not this term

- Real-time webcam stream matching.
- Live web scraping or auto-downloading images from Instagram, Wikipedia, or external APIs.
- Web UI / React frontend dashboard (strictly local CLI + HTML report generation).
- Mobile app or cloud-hosted API deployment.
- Advanced age or gender filtering options.

## 4. How we would know it works

- Given an image without any recognizable face, the tool exits with status 1 and prints `Error: No face detected in input image`.
- Given two identical copies of the same face image (query vs dataset), the top result returned always has a 100% (1.00) similarity score.
- Given a valid image input, the generated `summary.html` contains exactly 3 image tags pointing to valid output paths and non-negative similarity scores.

## 5. What could stop this

- **Privacy & GDPR / legal risk:** storing or using sensitive real-world personal data without consent. Mitigation: the tool uses a publicly available, open-license dataset (e.g., LFW - Labeled Faces in the Wild - or a small royalty-free synthetic dataset) and runs entirely offline on local files without uploading data anywhere.
- **Performance bottleneck:** extracting embeddings for hundreds of images on every run. Mitigation: the tool pre-computes and caches vector embeddings into a local `embeddings.json` file, so matching takes under a second.
