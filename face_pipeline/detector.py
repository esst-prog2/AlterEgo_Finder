"""Face localization using OpenCV's DNN face detector (Caffe SSD, res10_300x300)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
PROTOTXT_PATH = MODELS_DIR / "deploy.prototxt"
CAFFEMODEL_PATH = MODELS_DIR / "res10_300x300_ssd_iter_140000.caffemodel"

CONFIDENCE_THRESHOLD = 0.5

_net: Optional[cv2.dnn.Net] = None


def _get_net() -> cv2.dnn.Net:
    global _net
    if _net is None:
        _net = cv2.dnn.readNetFromCaffe(str(PROTOTXT_PATH), str(CAFFEMODEL_PATH))
    return _net


def detect_face(image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detect the most confident face in ``image``.

    Returns the bounding box as ``(x1, y1, x2, y2)`` pixel coordinates, or
    ``None`` if no face is detected above ``CONFIDENCE_THRESHOLD``.
    """
    net = _get_net()
    h, w = image.shape[:2]

    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (300, 300)),
        scalefactor=1.0,
        size=(300, 300),
        mean=(104.0, 177.0, 123.0),
    )
    net.setInput(blob)
    detections = net.forward()

    best_confidence = 0.0
    best_box: Optional[Tuple[int, int, int, int]] = None

    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < CONFIDENCE_THRESHOLD or confidence <= best_confidence:
            continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            continue

        best_confidence = confidence
        best_box = (x1, y1, x2, y2)

    return best_box
