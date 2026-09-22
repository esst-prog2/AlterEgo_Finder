from pathlib import Path

import cv2
import numpy as np

from face_pipeline.detector import detect_face

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_face_in_known_face_image():
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    result = detect_face(image)
    assert result is not None
    x1, y1, x2, y2 = result.box
    assert x2 > x1
    assert y2 > y1
    assert result.landmarks.shape == (5, 2)


def test_returns_none_for_image_with_no_face():
    blank = np.full((300, 300, 3), 255, dtype=np.uint8)
    assert detect_face(blank) is None


def test_detects_face_regardless_of_image_size():
    # YuNet's input size isn't fixed at load time; setInputSize() must be
    # called per image. Verify detection works on two differently-sized
    # fixture images (a regression guard for that gotcha).
    small = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    large = cv2.imread(str(FIXTURES / "obama_query.jpg"))
    assert small.shape != large.shape  # sanity: fixtures are actually different sizes

    assert detect_face(small) is not None
    assert detect_face(large) is not None
