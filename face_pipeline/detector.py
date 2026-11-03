"""Face localization using YuNet (bbox + 5 landmarks in one pass)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

from face_pipeline.images import read_file_bytes
from face_pipeline.weights import ensure_weight

YUNET_MODEL_FILENAME = "face_detection_yunet_2023mar.onnx"

SCORE_THRESHOLD = 0.8
NMS_THRESHOLD = 0.3
TOP_K = 5000
# YuNet scores very large faces lower: real phone photos scored 0.58 and 0.798 at
# full size against the cutoff, and over 0.8 at 1600 px. Tried largest first when
# full size finds nothing, each as the copy's longest side.
RETRY_SIZES = (1600, 1024, 640)
# A photo on its side or upside down can still "find" a face, with a useless embedding
# (at 180 degrees, 97 of 150 LFW photos), so a retry when nothing is found is not enough.
# YuNet is more confident the right way up: of four orientations, upright scored highest
# on 300 of 300 LFW photos, by at least 0.024. Compared on a copy of this longest side,
# since scores change with size; a photo turns only for a win above the margin.
TURN_CHECK_SIZE = 640
TURN_MARGIN = 0.02

# YuNet's native landmark order.
LANDMARK_ORDER = ("right_eye", "left_eye", "nose", "right_mouth", "left_mouth")

_detector: Optional[cv2.FaceDetectorYN] = None


def _get_detector() -> cv2.FaceDetectorYN:
    global _detector
    if _detector is None:
        model_path = ensure_weight(YUNET_MODEL_FILENAME)
        _detector = cv2.FaceDetectorYN.create(
            "onnx", read_file_bytes(model_path), np.empty(0, dtype=np.uint8),
            (320, 320), SCORE_THRESHOLD, NMS_THRESHOLD, TOP_K,
        )
    return _detector


@dataclass
class DetectedFace:
    box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    # (5, 2) array of (x, y), in YuNet's native order: right_eye, left_eye,
    # nose, right_mouth, left_mouth. See LANDMARK_ORDER.
    landmarks: np.ndarray


def pick_largest_face(faces: np.ndarray) -> np.ndarray:
    """Return the YuNet row (x, y, w, h, landmarks..., score) with the largest
    box area. In a query photo the subject is the largest face; a printed face
    or a bystander can score higher but is smaller.
    """
    return faces[np.argmax(faces[:, 2] * faces[:, 3])]


def _faces_at_size(image: np.ndarray) -> Optional[np.ndarray]:
    """One YuNet pass over ``image`` as it is: its rows, or None if no faces."""
    detector = _get_detector()
    h, w = image.shape[:2]
    detector.setInputSize((w, h))

    _, faces = detector.detect(image)
    return None if faces is None or len(faces) == 0 else faces


def _find_faces(image: np.ndarray) -> Optional[Tuple[np.ndarray, float]]:
    """Faces at full size or, failing that, on the largest smaller copy that has
    any, with the scale from ``image`` to the size they were found at.

    Full size comes first, so a face found there gives the same result as with no
    retry. Copies are never enlarged, so small images only get the one pass.
    """
    faces = _faces_at_size(image)
    if faces is not None:
        return faces, 1.0

    longest = max(image.shape[:2])
    for size in RETRY_SIZES:
        if size < longest:
            scale = size / longest
            copy = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            faces = _faces_at_size(copy)
            if faces is not None:
                return faces, scale
    return None


def _best_face_score(image: np.ndarray) -> Optional[float]:
    """The most confident face's score, of any size. The largest face can be a bystander
    cut off at the edge, whose low score let upside-down copies of two upright LFW photos win.
    """
    faces = _faces_at_size(image)
    return None if faces is None else float(faces[:, -1].max())


def _choose_turn(image: np.ndarray) -> int:
    """How many quarter turns (``np.rot90``'s k) put ``image`` the right way up: 0 unless
    another orientation clearly beats it as it is.

    A face missed as it is on the small copy may just be tiny, and a turned copy may give
    a false one, so a turn then also needs ``image`` itself to have no face.
    """
    longest = max(image.shape[:2])
    small = image
    if longest > TURN_CHECK_SIZE:
        scale = TURN_CHECK_SIZE / longest
        small = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    as_it_is = _best_face_score(small)
    scores = {k: _best_face_score(np.rot90(small, k).copy()) for k in (1, 2, 3)}
    scores = {k: score for k, score in scores.items() if score is not None}
    if not scores:
        return 0
    best = max(scores, key=scores.get)
    if as_it_is is None:
        return best if _find_faces(image) is None else 0
    return best if scores[best] > as_it_is + TURN_MARGIN else 0


def _from_turned(points: np.ndarray, k: int, h: int, w: int) -> np.ndarray:
    """(x, y) rows in ``np.rot90(image, k)`` back in ``image``, which is ``h`` by ``w``."""
    x, y = points[:, 0], points[:, 1]
    if k == 1:
        return np.stack([w - 1 - y, x], axis=1)
    if k == 2:
        return np.stack([w - 1 - x, h - 1 - y], axis=1)
    return np.stack([y, h - 1 - x], axis=1)


def detect_face(image: np.ndarray) -> Optional[DetectedFace]:
    """Detect the largest face in ``image`` (see ``pick_largest_face``), turning the photo
    first if it is on its side or upside down (see ``_choose_turn``).

    Returns a ``DetectedFace`` (bounding box + 5 landmarks, in ``image``'s own
    coordinates), or ``None`` if no face is detected above ``SCORE_THRESHOLD``.
    """
    turn = _choose_turn(image)
    working = np.rot90(image, turn).copy() if turn else image
    found = _find_faces(working)
    if found is None:
        return None

    faces, scale = found
    h, w = image.shape[:2]
    best = pick_largest_face(faces)
    x, y, box_w, box_h = best[0:4] / scale
    landmarks = best[4:14].reshape(5, 2) / scale
    if turn:
        corners = _from_turned(np.array([[x, y], [x + box_w, y + box_h]]), turn, h, w)
        x, y = corners.min(axis=0)
        box_w, box_h = corners.max(axis=0) - corners.min(axis=0)
        landmarks = _from_turned(landmarks, turn, h, w)
    x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
    x2, y2 = min(w, int(round(x + box_w))), min(h, int(round(y + box_h)))
    if x2 <= x1 or y2 <= y1:
        return None

    return DetectedFace(box=(x1, y1, x2, y2), landmarks=landmarks)
