# Vendored model weights

These files are vendored directly in the repo (see
`openspec/changes/add-face-matching-cli/design.md`) rather than downloaded
on first run, to keep `match.py` runnable offline.

## Face detector — OpenCV DNN (Caffe SSD, res10_300x300)

- `deploy.prototxt`
  Source: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/face_detector/deploy.prototxt
- `res10_300x300_ssd_iter_140000.caffemodel`
  Source: https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
  SHA1: `15aa726b4d46d9f023526d85537db81cbc8dd566`

## Face embedding — OpenFace nn4.small2.v1 (128-d)

- `nn4.small2.v1.t7`
  Source: https://storage.cmusatyalab.org/openface-models/nn4.small2.v1.t7
  Size: 31,510,785 bytes
  MD5: `c95bfd8cc1adf05210e979ff623013b6`

To re-vendor, re-download from the source URLs above and verify against the
listed checksum.
