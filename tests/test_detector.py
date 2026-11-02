from pathlib import Path

import cv2
import numpy as np

from face_pipeline import detector
from face_pipeline.detector import detect_face, pick_largest_face
from face_pipeline.embedder import extract_embedding

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


# --- large faces in large photos ---------------------------------------------------
# YuNet scores very large faces lower. obama_1.jpg enlarged to 3000 px is missed at
# full size and found on a smaller copy, as real phone photos were (2026-11-02).


def _enlarged(longest=3000):
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    scale = longest / max(image.shape[:2])
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC), scale


def test_large_face_missed_at_full_size_is_found_in_full_size_coordinates():
    original = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    reference = detector.detect_face(original)
    image, scale = _enlarged()
    assert detector._faces_at_size(image) is None  # the bug: nothing at full size

    found = detector.detect_face(image)

    assert found is not None
    height, width = image.shape[:2]
    x1, y1, x2, y2 = found.box
    assert 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height
    # Same face in the same place as on the original photo, scaled up.
    tolerance = 0.05 * width
    assert np.allclose(found.landmarks, reference.landmarks * scale, atol=tolerance)


def test_large_face_gives_the_same_identity():
    original = extract_embedding(cv2.imread(str(FIXTURES / "obama_1.jpg")))
    enlarged = extract_embedding(_enlarged()[0])
    similarity = original @ enlarged / (np.linalg.norm(original) * np.linalg.norm(enlarged))
    assert similarity > 0.9


def _fake_faces(found_at_longest, row=None, calls=None):
    """A stand-in for one detection pass: finds `row` only at one image size."""

    def faces_at_size(image):
        longest = max(image.shape[:2])
        if calls is not None:
            calls.append(longest)
        if longest == found_at_longest:
            return np.array([row], dtype=np.float32)
        return None

    return faces_at_size


def _row(x=10.0, y=20.0, w=100.0, h=120.0):
    landmarks = [30.0, 40.0, 70.0, 40.0, 50.0, 60.0, 35.0, 90.0, 65.0, 90.0]
    return [x, y, w, h] + landmarks + [0.9]


def test_sizes_are_tried_largest_first_and_stop_at_the_first_hit(monkeypatch):
    calls = []
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(1024, _row(), calls))

    assert detector.detect_face(np.zeros((1500, 3000, 3), dtype=np.uint8)) is not None

    assert calls == [3000, 1600, 1024]


def test_only_sizes_below_the_image_are_tried(monkeypatch):
    calls = []
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(None, calls=calls))

    assert detector.detect_face(np.zeros((1200, 900, 3), dtype=np.uint8)) is None

    assert calls == [1200, 1024, 640]


def test_face_found_at_full_size_means_no_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(3000, _row(), calls))

    assert detector.detect_face(np.zeros((1500, 3000, 3), dtype=np.uint8)) is not None

    assert calls == [3000]


def test_small_image_is_never_retried(monkeypatch):
    # LFW's 250-px images: why calibration cannot change.
    calls = []
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(None, calls=calls))

    assert detector.detect_face(np.zeros((250, 250, 3), dtype=np.uint8)) is None

    assert calls == [250]


def test_box_and_landmarks_are_mapped_back_from_the_copy(monkeypatch):
    # Found on a 1600-px copy of a 3200-px image, so coordinates double.
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(1600, _row()))

    found = detector.detect_face(np.zeros((2000, 3200, 3), dtype=np.uint8))

    assert found.box == (20, 40, 220, 280)
    assert found.landmarks[0].tolist() == [60.0, 80.0]
    assert found.landmarks[4].tolist() == [130.0, 180.0]


def test_box_is_clipped_to_the_full_image_after_mapping_back(monkeypatch):
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(1600, _row(x=1550.0, y=-5.0, w=100.0, h=100.0)))

    found = detector.detect_face(np.zeros((2000, 3200, 3), dtype=np.uint8))

    assert found.box == (3100, 0, 3200, 190)


def test_large_blank_image_has_no_face():
    assert detector.detect_face(np.full((3000, 3000, 3), 255, dtype=np.uint8)) is None
