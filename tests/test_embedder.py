from pathlib import Path

import cv2
import numpy as np

from face_pipeline.alignment import align_face
from face_pipeline.detector import detect_face
from face_pipeline.embedder import EMBEDDING_SIZE, embed_face

FIXTURES = Path(__file__).parent / "fixtures"


def _aligned_face():
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    detected = detect_face(image)
    return align_face(image, detected)


def test_embedding_has_expected_shape():
    vec = embed_face(_aligned_face())
    assert vec.shape == (EMBEDDING_SIZE,)


def test_embedding_is_deterministic():
    aligned = _aligned_face()
    vec1 = embed_face(aligned)
    vec2 = embed_face(aligned)
    assert np.array_equal(vec1, vec2)
