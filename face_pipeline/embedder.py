"""128-d face embedding extraction using OpenFace (nn4.small2.v1)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from face_pipeline.detector import detect_face

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
EMBEDDER_MODEL_PATH = MODELS_DIR / "nn4.small2.v1.t7"

EMBEDDING_SIZE = 128
INPUT_SIZE = (96, 96)

_net: Optional[cv2.dnn.Net] = None


def _get_net() -> cv2.dnn.Net:
    global _net
    if _net is None:
        _net = cv2.dnn.readNetFromTorch(str(EMBEDDER_MODEL_PATH))
    return _net


def embed_face(image: np.ndarray, box: Tuple[int, int, int, int]) -> np.ndarray:
    """Extract a 128-d embedding for the face at ``box`` within ``image``."""
    x1, y1, x2, y2 = box
    face = image[y1:y2, x1:x2]

    net = _get_net()
    blob = cv2.dnn.blobFromImage(
        face,
        scalefactor=1.0 / 255,
        size=INPUT_SIZE,
        mean=(0, 0, 0),
        swapRB=True,
        crop=False,
    )
    net.setInput(blob)
    embedding = net.forward()
    return embedding.reshape(EMBEDDING_SIZE).astype(np.float32)


class NoFaceDetectedError(Exception):
    """Raised when no face can be detected in an image."""


def extract_embedding(image: np.ndarray) -> np.ndarray:
    """Detect the face in ``image`` and return its 128-d embedding.

    Raises ``NoFaceDetectedError`` if no face is detected.
    """
    box = detect_face(image)
    if box is None:
        raise NoFaceDetectedError()
    return embed_face(image, box)
