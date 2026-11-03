"""Writing test images on any path: cv2.imwrite fails silently on non-ASCII ones."""

from pathlib import Path

import cv2
import numpy as np


def write_image(path: Path, image: np.ndarray) -> None:
    ok, encoded = cv2.imencode(Path(path).suffix, image)
    assert ok
    encoded.tofile(str(path))
