"""Aligns a detected face to the canonical 112x112 ArcFace pose via a
5-point affine warp.
"""

from __future__ import annotations

import cv2
import numpy as np

from face_pipeline.detector import DetectedFace

ALIGNED_SIZE = 112

# Standard ArcFace 5-point reference template for a 112x112 output.
#
# Empirically verified (not just trusted from docs) to map directly,
# index-for-index, onto YuNet's own landmark order (right_eye, left_eye,
# nose, right_mouth, left_mouth) -- see the design.md decision log for
# this change. A prose description found while researching this claimed
# the reference points were in (left_eye, right_eye, nose, left_mouth,
# right_mouth) order, which reads as the opposite pairing; that
# description was misleading. Fitting a transform through all 5 points
# and checking the residual (not just "does it run") is what caught this.
REFERENCE_LANDMARKS = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


def align_face(image: np.ndarray, detected: DetectedFace) -> np.ndarray:
    """Warp the detected face to a 112x112 canonical pose for ArcFace-family
    embedding, using YuNet's 5 landmarks directly against
    ``REFERENCE_LANDMARKS`` (same index order, verified empirically).
    """
    transform, _ = cv2.estimateAffinePartial2D(detected.landmarks, REFERENCE_LANDMARKS)
    aligned = cv2.warpAffine(image, transform, (ALIGNED_SIZE, ALIGNED_SIZE))
    return aligned
