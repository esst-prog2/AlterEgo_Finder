"""The program works from any folder, and a stalled weight download fails.

OpenCV cannot open a non-ASCII path on Windows: images read as nothing and models
fail to load (measured 2026-11-03). Elsewhere these still pin the behaviour.
"""

import io
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

import face_pipeline.detector as detector
import face_pipeline.embedder as embedder
import face_pipeline.weights as weights
from face_pipeline.calibration import embed_calibration_dataset
from face_pipeline.embedder import extract_embedding
from face_pipeline.index import build_index
from face_pipeline.weights import ModelWeightError

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
QUERY = FIXTURES / "obama_query.jpg"
ACCENTED = "György Árvíztűrő"
OUTSIDE_THE_CONSOLE = "山田"  # not in Windows' usual console encodings


@pytest.fixture
def folder(tmp_path):
    path = tmp_path / ACCENTED
    path.mkdir()
    return path


def test_read_image_reads_an_accented_path_like_a_plain_one(tmp_path, folder):
    from face_pipeline.images import read_image

    plain = tmp_path / "plain.jpg"
    shutil.copy(QUERY, plain)
    shutil.copy(QUERY, folder / "photo.jpg")

    image = read_image(folder / "photo.jpg")

    assert image is not None
    assert np.array_equal(image, cv2.imread(str(plain)))


def test_read_image_gives_none_for_what_cannot_be_read(folder):
    from face_pipeline.images import read_image

    (folder / "empty.jpg").write_bytes(b"")
    (folder / "text.jpg").write_bytes(b"not an image")

    assert read_image(folder / "missing.jpg") is None
    assert read_image(folder / "empty.jpg") is None
    assert read_image(folder / "text.jpg") is None
    assert read_image(folder) is None  # a directory


@pytest.fixture(scope="module")
def accented_models(tmp_path_factory):
    models = tmp_path_factory.mktemp("models") / ACCENTED
    shutil.copytree(weights.MODELS_DIR, models, ignore=shutil.ignore_patterns("*.part"))
    return models


def test_both_models_load_from_an_accented_folder_with_the_same_result(accented_models, monkeypatch):
    from face_pipeline.images import read_image

    image = read_image(FIXTURES / "obama_1.jpg")
    expected = extract_embedding(image)

    monkeypatch.setattr(weights, "MODELS_DIR", accented_models)
    monkeypatch.setattr(weights, "MANIFEST_PATH", accented_models / "manifest.json")
    monkeypatch.setattr(detector, "_detector", None)
    monkeypatch.setattr(embedder, "_net", None)

    assert np.array_equal(extract_embedding(image), expected)


def test_a_dataset_in_an_accented_folder_keeps_all_its_images(folder):
    plain = build_index(FIXTURES / "dataset")
    dataset = folder / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset)
    shutil.rmtree(dataset / ".matchcache", ignore_errors=True)
    (next(p for p in dataset.iterdir() if p.is_dir())).rename(dataset / ACCENTED)

    index = build_index(dataset)

    assert len(index.entries) == len(plain.entries) > 0
    assert ACCENTED in {e.person for e in index.entries}


def test_calibration_reads_an_accented_folder(folder):
    calibration = folder / "calibration"
    shutil.copytree(FIXTURES / "calibration", calibration)
    plain = embed_calibration_dataset(FIXTURES / "calibration")

    assert {k: len(v) for k, v in embed_calibration_dataset(calibration).items()} == {
        k: len(v) for k, v in plain.items()
    }


def _match(image: Path, dataset: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "match.py"), "--image", str(image), "--dataset", str(dataset),
         "--threshold-low", "0", "--threshold-high", "1", "--report-out", str(tmp_path / "r.html")],
        cwd=REPO_ROOT, capture_output=True,
    )


def test_match_runs_on_an_accented_query_and_dataset(folder, tmp_path):
    shutil.copy(QUERY, folder / "photo.jpg")
    dataset = folder / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset)
    shutil.rmtree(dataset / ".matchcache", ignore_errors=True)

    result = _match(folder / "photo.jpg", dataset, tmp_path)

    assert result.returncode == 0, result.stderr
    assert b"Barack_Obama" in result.stdout
    assert b"HIGH_CONFIDENCE" not in result.stdout
    assert (tmp_path / "r.html").stat().st_size > 1000  # the report has both images


def test_match_prints_a_person_name_the_console_cannot_encode(folder, tmp_path):
    dataset = folder / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset)
    shutil.rmtree(dataset / ".matchcache", ignore_errors=True)
    (dataset / "Barack_Obama").rename(dataset / OUTSIDE_THE_CONSOLE)

    result = _match(QUERY, dataset, tmp_path)

    assert result.returncode == 0, result.stderr


# --- the weight download ----------------------------------------------------------


class _Stalling(io.BytesIO):
    """A response that sends one chunk and then stops."""

    def read(self, *args):
        if self.tell() == 0:
            return super().read(*args)
        raise socket.timeout("timed out")


def test_a_stalled_download_fails_and_leaves_nothing_behind(tmp_path, monkeypatch):
    monkeypatch.setattr(weights.urllib.request, "urlopen", lambda *a, **k: _Stalling(b"half a model"))

    with pytest.raises(ModelWeightError, match="fake.onnx"):
        weights._download("https://example.invalid/fake.onnx", tmp_path / "fake.onnx")

    assert list(tmp_path.iterdir()) == []


def test_the_download_sets_a_timeout_and_writes_the_whole_file(tmp_path, monkeypatch):
    seen = {}

    def opened(url, timeout=None):
        seen["timeout"] = timeout
        return io.BytesIO(b"a whole model")

    monkeypatch.setattr(weights.urllib.request, "urlopen", opened)

    weights._download("https://example.invalid/fake.onnx", tmp_path / "fake.onnx")

    assert seen["timeout"] == weights.DOWNLOAD_TIMEOUT_S > 0
    assert (tmp_path / "fake.onnx").read_bytes() == b"a whole model"
    assert [p.name for p in tmp_path.iterdir()] == ["fake.onnx"]


# --- staying fixed ----------------------------------------------------------------


def test_the_program_never_gives_opencv_a_path():
    # A new call would pass every test on a machine with plain ASCII paths.
    files = [REPO_ROOT / f for f in ("app.py", "match.py", "calibrate.py", "setup_data.py")]
    files += sorted((REPO_ROOT / "face_pipeline").glob("*.py"))
    forbidden = ("cv2.imread(", "cv2.imwrite(", "readNetFromONNX(str", "FaceDetectorYN.create(\n            str")
    found = [(f.name, word) for f in files for word in forbidden
             if word in f.read_text(encoding="utf-8").replace("\r\n", "\n")]
    assert found == []


def test_the_manifest_still_names_both_models():
    names = set(json.loads((weights.MODELS_DIR / "manifest.json").read_text()))
    assert {detector.YUNET_MODEL_FILENAME, embedder.EMBEDDER_MODEL_FILENAME} <= names


def _with_exif_rotation(jpeg: bytes, orientation: int) -> bytes:
    """``jpeg`` with an EXIF block saying how to rotate it, as phone cameras write."""
    tiff = b"II*\x00\x08\x00\x00\x00\x01\x00\x12\x01\x03\x00\x01\x00\x00\x00" + bytes([orientation, 0, 0, 0]) + b"\x00" * 4
    block = b"Exif\x00\x00" + tiff
    return jpeg[:2] + b"\xff\xe1" + (len(block) + 2).to_bytes(2, "big") + block + jpeg[2:]


def test_read_image_turns_a_phone_photo_upright_as_opencv_does(tmp_path, folder):
    # Phone photos depend on this, and nothing else in the project's data has the tag.
    from face_pipeline.images import read_image

    upright = read_image(QUERY)
    rotated = _with_exif_rotation(QUERY.read_bytes(), 6)  # 6: turn 90 degrees clockwise
    plain, accented = tmp_path / "phone.jpg", folder / "phone.jpg"
    plain.write_bytes(rotated)
    accented.write_bytes(rotated)

    image = read_image(accented)

    assert np.array_equal(image, cv2.imread(str(plain)))
    assert np.array_equal(image, cv2.rotate(upright, cv2.ROTATE_90_CLOCKWISE))
