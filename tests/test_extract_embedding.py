from pathlib import Path

import cv2
import numpy as np
import pytest

from face_pipeline.embedder import EMBEDDING_SIZE, NoFaceDetectedError, extract_embedding

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_embedding_returns_128d_vector_for_face_present():
    image = cv2.imread(str(FIXTURES / "obama_1.jpg"))
    vec = extract_embedding(image)
    assert vec.shape == (EMBEDDING_SIZE,)


def test_extract_embedding_raises_for_no_face_present():
    blank = np.full((300, 300, 3), 255, dtype=np.uint8)
    with pytest.raises(NoFaceDetectedError):
        extract_embedding(blank)
