"""Face localization using YuNet (bbox + 5 landmarks in one pass)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
YUNET_MODEL_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"

SCORE_THRESHOLD = 0.9
NMS_THRESHOLD = 0.3
TOP_K = 5000

# YuNet's native landmark order.
LANDMARK_ORDER = ("right_eye", "left_eye", "nose", "right_mouth", "left_mouth")

_detector: Optional[cv2.FaceDetectorYN] = None


def _get_detector() -> cv2.FaceDetectorYN:
    global _detector
    if _detector is None:
        _detector = cv2.FaceDetectorYN.create(
            str(YUNET_MODEL_PATH), "", (320, 320), SCORE_THRESHOLD, NMS_THRESHOLD, TOP_K
        )
    return _detector


@dataclass
class DetectedFace:
    box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    # (5, 2) array of (x, y), in YuNet's native order: right_eye, left_eye,
    # nose, right_mouth, left_mouth. See LANDMARK_ORDER.
    landmarks: np.ndarray


def detect_face(image: np.ndarray) -> Optional[DetectedFace]:
    """Detect the most confident face in ``image``.

    Returns a ``DetectedFace`` (bounding box + 5 landmarks), or ``None`` if
    no face is detected above ``SCORE_THRESHOLD``.
    """
    detector = _get_detector()
    h, w = image.shape[:2]
    detector.setInputSize((w, h))

    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        return None

    # detect() returns faces sorted by descending score; take the top one.
    best = faces[0]
    x, y, box_w, box_h = best[0:4]
    x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
    x2, y2 = min(w, int(round(x + box_w))), min(h, int(round(y + box_h)))
    if x2 <= x1 or y2 <= y1:
        return None

    landmarks = best[4:14].reshape(5, 2)
    return DetectedFace(box=(x1, y1, x2, y2), landmarks=landmarks)
