import hashlib
import json

import pytest

import face_pipeline.weights as weights_module
from face_pipeline.weights import ModelWeightError, ensure_weight


@pytest.fixture
def isolated_models_dir(tmp_path, monkeypatch):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    manifest_path = models_dir / "manifest.json"
    monkeypatch.setattr(weights_module, "MODELS_DIR", models_dir)
    monkeypatch.setattr(weights_module, "MANIFEST_PATH", manifest_path)
    return models_dir, manifest_path


def _write_manifest(manifest_path, entries):
    manifest_path.write_text(json.dumps(entries))


def test_ensure_weight_returns_existing_valid_file_without_downloading(
    isolated_models_dir, monkeypatch
):
    models_dir, manifest_path = isolated_models_dir
    content = b"fake model bytes"
    file_path = models_dir / "fake.onnx"
    file_path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    _write_manifest(
        manifest_path,
        {"fake.onnx": {"url": "https://example.invalid/fake.onnx", "sha256": sha256}},
    )

    def fail_download(*args, **kwargs):
        raise AssertionError("should not download when a valid file already exists")

    monkeypatch.setattr(weights_module, "_download", fail_download)

    result = ensure_weight("fake.onnx")
    assert result == file_path


def test_ensure_weight_downloads_when_missing(isolated_models_dir, monkeypatch):
    models_dir, manifest_path = isolated_models_dir
    content = b"downloaded model bytes"
    sha256 = hashlib.sha256(content).hexdigest()
    _write_manifest(
        manifest_path,
        {"fake.onnx": {"url": "https://example.invalid/fake.onnx", "sha256": sha256}},
    )

    def fake_download(url, destination):
        destination.write_bytes(content)

    monkeypatch.setattr(weights_module, "_download", fake_download)

    result = ensure_weight("fake.onnx")
    assert result == models_dir / "fake.onnx"
    assert result.read_bytes() == content


def test_ensure_weight_raises_on_checksum_mismatch_and_removes_bad_file(
    isolated_models_dir,
):
    models_dir, manifest_path = isolated_models_dir
    file_path = models_dir / "fake.onnx"
    file_path.write_bytes(b"corrupted content")
    _write_manifest(
        manifest_path,
        {"fake.onnx": {"url": "https://example.invalid/fake.onnx", "sha256": "0" * 64}},
    )

    with pytest.raises(ModelWeightError, match="Checksum mismatch"):
        ensure_weight("fake.onnx")

    assert not file_path.exists()


def test_ensure_weight_raises_on_download_failure(isolated_models_dir, monkeypatch):
    models_dir, manifest_path = isolated_models_dir
    _write_manifest(
        manifest_path,
        {"fake.onnx": {"url": "https://example.invalid/fake.onnx", "sha256": "0" * 64}},
    )

    def fail_download(url, destination):
        raise ModelWeightError(
            f"Failed to download model weight file {destination.name} from {url}: simulated failure"
        )

    monkeypatch.setattr(weights_module, "_download", fail_download)

    with pytest.raises(ModelWeightError, match="fake.onnx"):
        ensure_weight("fake.onnx")
