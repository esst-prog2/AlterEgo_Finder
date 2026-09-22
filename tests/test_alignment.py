from pathlib import Path

import cv2
import numpy as np

from face_pipeline.alignment import ALIGNED_SIZE, REFERENCE_LANDMARKS, align_face
from face_pipeline.detector import DetectedFace, detect_face

FIXTURES = Path(__file__).parent / "fixtures"

# A tolerance loose enough for a real photo's similarity-transform residual,
# but tight enough that a swapped left/right landmark pairing (which shows
# up as tens of pixels of error, not single digits) would fail this check.
LANDMARK_TOLERANCE_PX = 10.0


def test_align_face_produces_112x112_image():
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    detected = detect_face(image)
    aligned = align_face(image, detected)
    assert aligned.shape == (ALIGNED_SIZE, ALIGNED_SIZE, 3)


def test_alignment_landmark_correspondence_is_correct():
    """Regression guard for the landmark-pairing bug found while building
    this: fit a transform through the detected landmarks and the reference
    template, then check every point lands close to where it should -- a
    swapped left/right pairing produces tens of pixels of residual, not a
    crash, so this must check distances, not just that alignment runs.
    """
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    detected: DetectedFace = detect_face(image)

    transform, _ = cv2.estimateAffinePartial2D(detected.landmarks, REFERENCE_LANDMARKS)
    ones = np.ones((5, 1), dtype=np.float32)
    projected = (transform @ np.hstack([detected.landmarks, ones]).T).T

    residuals = np.linalg.norm(projected - REFERENCE_LANDMARKS, axis=1)
    assert residuals.max() < LANDMARK_TOLERANCE_PX, (
        f"landmark correspondence looks wrong (residuals={residuals}); "
        "a correct pairing should fit within a few pixels"
    )
