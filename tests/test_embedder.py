from pathlib import Path

import cv2
import numpy as np

from face_pipeline.detector import detect_face
from face_pipeline.embedder import EMBEDDING_SIZE, embed_face

FIXTURES = Path(__file__).parent / "fixtures"


def _load_face_box():
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    box = detect_face(image)
    assert box is not None
    return image, box


def test_embedding_has_expected_shape():
    image, box = _load_face_box()
    vec = embed_face(image, box)
    assert vec.shape == (EMBEDDING_SIZE,)


def test_embedding_is_deterministic():
    image, box = _load_face_box()
    vec1 = embed_face(image, box)
    vec2 = embed_face(image, box)
    assert np.array_equal(vec1, vec2)
