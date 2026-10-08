from pathlib import Path

import cv2
import numpy as np

from face_pipeline.detector import detect_face, pick_largest_face

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


def _yunet_row(x, y, w, h, score):
    # YuNet row layout: x, y, w, h, 5 landmark (x, y) pairs, score.
    return [x, y, w, h] + [0.0] * 10 + [score]


def test_pick_largest_face_prefers_larger_box_over_higher_score():
    # Expected value (PLANNING_LOG.md, 2026-10-08), planted: the larger face
    # wins even though the smaller one scored higher.
    small = _yunet_row(296, 568, 40, 54, 0.95)
    large = _yunet_row(229, 245, 134, 171, 0.90)
    faces = np.array([small, large], dtype=np.float32)
    assert pick_largest_face(faces)[2:4].tolist() == [134, 171]


def test_detects_wearer_not_shirt_print_in_sunglasses_photo():
    # The user's own photo (HW5 step 6): sunglasses, head turned, and a
    # printed face on the T-shirt. Expected value (PLANNING_LOG.md,
    # 2026-10-08), read by eye: the user's head spans x 220-390, y 225-440;
    # the print is below y 515.
    image = cv2.imread(str(FIXTURES / "pk_sunglasses_shirt.jpg"))
    result = detect_face(image)
    assert result is not None
    x1, y1, x2, y2 = result.box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    assert 220 <= cx <= 390
    assert 225 <= cy <= 440
