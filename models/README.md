# Model weights

These `.onnx` files are **not** tracked in git (see `.gitignore`) — they're
downloaded automatically on first use by `face_pipeline/weights.py`, which
also re-verifies each file's SHA-256 checksum on every use (not just right
after downloading), and fails clearly rather than silently loading a bad
or missing file. See
`openspec/changes/fetch-model-weights-checksum/design.md` for the
reasoning (the ArcFace weights alone are 63MB — over GitHub's recommended
50MB file-size limit).

`models/manifest.json` is the single source of truth for each file's
source URL and expected checksum; this file just describes what each one
is for.

## Face detector + landmarks — YuNet

`face_detection_yunet_2023mar.onnx` (~227KB) — OpenCV's own officially
bundled/documented face detector, giving both a bounding box and 5
landmarks in one pass.

## Face embedding — ArcFace ResNet100, INT8 (512-d)

`arcfaceresnet100-11-int8.onnx` (~63MB) — INT8-quantized ArcFace,
expecting a 112×112, RGB, unnormalized-pixel input (see
`face_pipeline/embedder.py`'s docstring for why "unnormalized" specifically
matters here).

To fetch either file manually (outside the normal on-demand flow), run
`python -c "from face_pipeline.weights import ensure_weight; ensure_weight('<filename>')"`.
