from pathlib import Path

import cv2
import numpy as np
import pytest

from face_pipeline.images import read_image
from face_pipeline import detector
from face_pipeline.detector import detect_face, pick_largest_face
from face_pipeline.embedder import extract_embedding

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_face_in_known_face_image():
    image = read_image(FIXTURES / "obama_1.jpg")
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
    small = read_image(FIXTURES / "obama_1.jpg")
    large = read_image(FIXTURES / "obama_query.jpg")
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
    image = read_image(FIXTURES / "pk_sunglasses_shirt.jpg")
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
    image = read_image(FIXTURES / "obama_1.jpg")
    scale = longest / max(image.shape[:2])
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC), scale


def test_large_face_missed_at_full_size_is_found_in_full_size_coordinates():
    original = read_image(FIXTURES / "obama_1.jpg")
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
    original = extract_embedding(read_image(FIXTURES / "obama_1.jpg"))
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
    monkeypatch.setattr(detector, "_choose_turn", lambda image: 0)
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(1024, _row(), calls))

    assert detector.detect_face(np.zeros((1500, 3000, 3), dtype=np.uint8)) is not None

    assert calls == [3000, 1600, 1024]


def test_only_sizes_below_the_image_are_tried(monkeypatch):
    calls = []
    monkeypatch.setattr(detector, "_choose_turn", lambda image: 0)
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(None, calls=calls))

    assert detector.detect_face(np.zeros((1200, 900, 3), dtype=np.uint8)) is None

    assert calls == [1200, 1024, 640]


def test_face_found_at_full_size_means_no_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(detector, "_choose_turn", lambda image: 0)
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(3000, _row(), calls))

    assert detector.detect_face(np.zeros((1500, 3000, 3), dtype=np.uint8)) is not None

    assert calls == [3000]


def test_small_image_is_never_retried(monkeypatch):
    # LFW's 250-px images: why calibration cannot change.
    calls = []
    monkeypatch.setattr(detector, "_choose_turn", lambda image: 0)
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(None, calls=calls))

    assert detector.detect_face(np.zeros((250, 250, 3), dtype=np.uint8)) is None

    assert calls == [250]


def test_box_and_landmarks_are_mapped_back_from_the_copy(monkeypatch):
    # Found on a 1600-px copy of a 3200-px image, so coordinates double.
    monkeypatch.setattr(detector, "_choose_turn", lambda image: 0)
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(1600, _row()))

    found = detector.detect_face(np.zeros((2000, 3200, 3), dtype=np.uint8))

    assert found.box == (20, 40, 220, 280)
    assert found.landmarks[0].tolist() == [60.0, 80.0]
    assert found.landmarks[4].tolist() == [130.0, 180.0]


def test_box_is_clipped_to_the_full_image_after_mapping_back(monkeypatch):
    monkeypatch.setattr(detector, "_choose_turn", lambda image: 0)
    monkeypatch.setattr(detector, "_faces_at_size", _fake_faces(1600, _row(x=1550.0, y=-5.0, w=100.0, h=100.0)))

    found = detector.detect_face(np.zeros((2000, 3200, 3), dtype=np.uint8))

    assert found.box == (3100, 0, 3200, 190)


def test_large_blank_image_has_no_face():
    assert detector.detect_face(np.full((3000, 3000, 3), 255, dtype=np.uint8)) is None


# --- photos on their side or upside down (decided 2026-11-03) --------------------

# How a point (x, y) of an image h high and w wide moves under np.rot90(image, k).
_TURNED = {
    1: lambda x, y, h, w: (y, w - 1 - x),
    2: lambda x, y, h, w: (w - 1 - x, h - 1 - y),
    3: lambda x, y, h, w: (h - 1 - y, x),
}


@pytest.mark.parametrize("k", [1, 2, 3])
def test_a_turned_photo_is_found_in_the_coordinates_it_was_given(k):
    upright = read_image(FIXTURES / "obama_1.jpg")
    h, w = upright.shape[:2]
    expected = detect_face(upright).landmarks
    photo = np.rot90(upright, k).copy()

    found = detect_face(photo)

    assert found is not None
    x1, y1, x2, y2 = found.box
    assert 0 <= x1 < x2 <= photo.shape[1] and 0 <= y1 < y2 <= photo.shape[0]
    ux1, uy1, ux2, uy2 = detect_face(upright).box
    corners = np.array([_TURNED[k](ux1, uy1, h, w), _TURNED[k](ux2, uy2, h, w)])
    assert abs(x1 - corners[:, 0].min()) < 12 and abs(x2 - corners[:, 0].max()) < 12
    assert abs(y1 - corners[:, 1].min()) < 12 and abs(y2 - corners[:, 1].max()) < 12
    for (x, y), (fx, fy) in zip(expected, found.landmarks):
        ex, ey = _TURNED[k](x, y, h, w)
        assert abs(fx - ex) < 8 and abs(fy - ey) < 8


@pytest.mark.parametrize("k", [1, 2, 3])
def test_a_turned_photo_gives_about_the_same_embedding(k):
    upright = read_image(FIXTURES / "obama_1.jpg")
    a = extract_embedding(upright)
    b = extract_embedding(np.rot90(upright, k).copy())
    assert a @ b / (np.linalg.norm(a) * np.linalg.norm(b)) > 0.9


@pytest.mark.parametrize("name", ["obama_1.jpg", "obama_2.jpg", "obama_query.jpg", "biden_1.jpg", "pk_sunglasses_shirt.jpg"])
def test_an_upright_photo_is_not_turned(name):
    assert detector._choose_turn(read_image(FIXTURES / name)) == 0


def _scores_by_turn(scores):
    """A detection pass whose score depends on which corner is now top-left."""
    def faces_at_size(image):
        score = scores[int(image[0, 0, 0])]
        return None if score is None else np.array([_row()[:-1] + [score]], dtype=np.float32)
    return faces_at_size


def _marked_image():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[0, 0], image[0, 99], image[99, 99], image[99, 0] = 0, 1, 2, 3  # top-left under k = 0, 1, 2, 3
    return image


def test_a_clear_win_turns_and_one_within_the_margin_does_not(monkeypatch):
    margin = detector.TURN_MARGIN
    monkeypatch.setattr(detector, "_faces_at_size", _scores_by_turn([0.8, None, 0.8 + margin + 0.01, None]))
    assert detector._choose_turn(_marked_image()) == 2

    monkeypatch.setattr(detector, "_faces_at_size", _scores_by_turn([0.8, None, 0.8 + margin - 0.01, None]))
    assert detector._choose_turn(_marked_image()) == 0


def test_the_most_confident_turn_wins(monkeypatch):
    monkeypatch.setattr(detector, "_faces_at_size", _scores_by_turn([0.8, 0.85, 0.9, 0.95]))
    assert detector._choose_turn(_marked_image()) == 3


def test_no_face_any_way_up_stays_as_it_is(monkeypatch):
    monkeypatch.setattr(detector, "_faces_at_size", _scores_by_turn([None, None, None, None]))
    assert detector._choose_turn(_marked_image()) == 0


def _portrait_only(also_landscape_at=None):
    """Finds a face only once a 500 x 1000 photo is turned, or as it is at one size."""
    def faces_at_size(image):
        h, w = image.shape[:2]
        if h > w or w == also_landscape_at:
            return np.array([_row()], dtype=np.float32)
        return None
    return faces_at_size


def test_upright_found_only_at_full_size_is_not_turned(monkeypatch):
    # The face is missed on the small copy, where a turned copy gives one.
    monkeypatch.setattr(detector, "_faces_at_size", _portrait_only(also_landscape_at=1000))
    assert detector._choose_turn(np.zeros((500, 1000, 3), dtype=np.uint8)) == 0


def test_a_face_found_only_when_turned_turns(monkeypatch):
    monkeypatch.setattr(detector, "_faces_at_size", _portrait_only())
    assert detector._choose_turn(np.zeros((500, 1000, 3), dtype=np.uint8)) == 1


def test_the_choice_is_made_on_a_small_copy(monkeypatch):
    sizes = []

    def faces_at_size(image):
        sizes.append(max(image.shape[:2]))
        return np.array([_row()], dtype=np.float32)

    monkeypatch.setattr(detector, "_faces_at_size", faces_at_size)
    detector._choose_turn(np.zeros((1500, 3000, 3), dtype=np.uint8))
    assert sizes == [detector.TURN_CHECK_SIZE] * 4


def test_a_cut_off_bystander_does_not_make_an_upright_group_photo_turn(monkeypatch):
    # Two LFW photos turned wrongly when only the largest face's score counted: a big
    # face cut off at the edge scored low, though a clear face was right beside it.
    def faces_at_size(image):
        if int(image[0, 0, 0]) == 0:  # as it is: a big low-scoring face and a small sharp one
            return np.array([_row(w=200.0, h=200.0)[:-1] + [0.81], _row(w=50.0, h=50.0)[:-1] + [0.95]], dtype=np.float32)
        return np.array([_row()[:-1] + [0.86]], dtype=np.float32)

    monkeypatch.setattr(detector, "_faces_at_size", faces_at_size)
    assert detector._choose_turn(_marked_image()) == 0

