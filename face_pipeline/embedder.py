"""512-d face embedding extraction using ArcFace ResNet100 (INT8)."""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from face_pipeline.alignment import ALIGNED_SIZE, align_face
from face_pipeline.detector import detect_face
from face_pipeline.weights import ensure_weight

EMBEDDER_MODEL_FILENAME = "arcfaceresnet100-11-int8.onnx"

EMBEDDING_SIZE = 512

# Preprocessing for this specific ONNX Model Zoo export (LResNet100E-IR /
# ArcFace@ms1m-refine-v2): RGB, 112x112, raw pixel values with NO mean
# subtraction or scaling. This was verified empirically, not from docs --
# several sources describe a (pixel - 127.5) / 128.0 normalization (the
# convention for newer insightface models), but applying that here collapses
# same-person and different-person similarity into the same ~0.95-0.97
# band with no separation. Raw 0-255 values give a clean, well-separated
# distribution (same-person ~0.7, different-person ~-0.07 on this
# project's fixtures) -- see design.md.
_PIXEL_MEAN = (0.0, 0.0, 0.0)
_PIXEL_SCALE = 1.0

_net: Optional[cv2.dnn.Net] = None


def _get_net() -> cv2.dnn.Net:
    global _net
    if _net is None:
        model_path = ensure_weight(EMBEDDER_MODEL_FILENAME)
        _net = cv2.dnn.readNetFromONNX(str(model_path))
    return _net


def embed_face(aligned_face: np.ndarray) -> np.ndarray:
    """Extract a 512-d embedding from an already-aligned 112x112 face crop."""
    net = _get_net()
    blob = cv2.dnn.blobFromImage(
        aligned_face,
        scalefactor=_PIXEL_SCALE,
        size=(ALIGNED_SIZE, ALIGNED_SIZE),
        mean=_PIXEL_MEAN,
        swapRB=True,
        crop=False,
    )
    net.setInput(blob)
    embedding = net.forward()
    return embedding.reshape(EMBEDDING_SIZE).astype(np.float32)


class NoFaceDetectedError(Exception):
    """Raised when no face can be detected in an image."""


def extract_embedding(image: np.ndarray) -> np.ndarray:
    """Detect, align, and embed the face in ``image``, returning a 512-d vector.

    Raises ``NoFaceDetectedError`` if no face is detected.
    """
    detected = detect_face(image)
    if detected is None:
        raise NoFaceDetectedError()
    aligned = align_face(image, detected)
    return embed_face(aligned)
