from pathlib import Path

import cv2
import numpy as np

from face_pipeline.detector import detect_face

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_face_in_known_face_image():
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    box = detect_face(image)
    assert box is not None
    x1, y1, x2, y2 = box
    assert x2 > x1
    assert y2 > y1


def test_returns_none_for_image_with_no_face():
    blank = np.full((300, 300, 3), 255, dtype=np.uint8)
    assert detect_face(blank) is None
