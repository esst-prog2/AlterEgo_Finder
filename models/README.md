# Vendored model weights

These files are vendored directly in the repo (see
`openspec/changes/switch-to-arcface-embedding/design.md`) rather than
downloaded on first run, to keep `match.py` runnable offline. (Asset
delivery — vendored vs. fetched-with-checksum — is being revisited
separately in `fetch-model-weights-checksum`.)

## Face detector + landmarks — YuNet

- `face_detection_yunet_2023mar.onnx`
  Source: https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
  Size: 232,589 bytes
  SHA-256: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`

## Face embedding — ArcFace ResNet100, INT8 (512-d)

- `arcfaceresnet100-11-int8.onnx`
  Source: https://huggingface.co/onnxmodelzoo/arcfaceresnet100-11-int8/resolve/main/arcfaceresnet100-11-int8.onnx
  Size: 65,764,892 bytes
  SHA-256: `c625ca68a422418c48aa84f73341337e0a92b111f327909005d1eec07c95f936`
  (No checksum is published upstream for this file; the value above was
  computed from the download and is what this project treats as canonical.)

To re-vendor, re-download from the source URLs above and verify against the
listed checksum.
