"""Reading images on any path.

OpenCV's own file functions cannot open a non-ASCII path on Windows and say nothing
about it, so the program reads the bytes itself and hands OpenCV those.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np


def read_file_bytes(path: Union[str, Path]) -> np.ndarray:
    """The file's bytes, as OpenCV's from-memory functions take them."""
    return np.fromfile(str(path), dtype=np.uint8)


def read_image(path: Union[str, Path]) -> Optional[np.ndarray]:
    """The image at ``path`` in BGR, or None if it is missing or not a readable image."""
    try:
        data = read_file_bytes(path)
    except OSError:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None
