import shutil
from pathlib import Path

import face_pipeline.index as index_module
from face_pipeline.index import EMBEDDING_SIZE, get_or_build_index

FIXTURES = Path(__file__).parent / "fixtures"


def _make_dataset(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset_dir)
    return dataset_dir


def test_build_index_produces_expected_row_count(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    index = index_module.build_index(dataset_dir)
    assert index.embeddings.shape == (3, EMBEDDING_SIZE)
    assert len(index.entries) == 3
    assert {e.person for e in index.entries} == {"Barack_Obama", "Joe_Biden"}


def test_get_or_build_index_writes_cache_files(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    get_or_build_index(dataset_dir)

    embeddings_path, manifest_path = index_module._cache_paths(dataset_dir)
    assert embeddings_path.exists()
    assert manifest_path.exists()


def test_cache_reused_if_fresh(tmp_path, monkeypatch):
    dataset_dir = _make_dataset(tmp_path)
    first = get_or_build_index(dataset_dir)

    calls = []
    original_build_index = index_module.build_index

    def spy_build_index(path):
        calls.append(path)
        return original_build_index(path)

    monkeypatch.setattr(index_module, "build_index", spy_build_index)

    second = get_or_build_index(dataset_dir)

    assert calls == []  # cache was reused, no rebuild triggered
    assert second.embeddings.shape == first.embeddings.shape
    assert [e.person for e in second.entries] == [e.person for e in first.entries]


def test_cache_rebuilt_if_stale(tmp_path, monkeypatch):
    dataset_dir = _make_dataset(tmp_path)
    get_or_build_index(dataset_dir)

    # Add a new file to the dataset, invalidating the cached manifest.
    shutil.copy(
        FIXTURES / "obama_query.jpg",
        dataset_dir / "Barack_Obama" / "Barack_Obama_0003.jpg",
    )

    calls = []
    original_build_index = index_module.build_index

    def spy_build_index(path):
        calls.append(path)
        return original_build_index(path)

    monkeypatch.setattr(index_module, "build_index", spy_build_index)

    rebuilt = get_or_build_index(dataset_dir)

    assert len(calls) == 1  # rebuild was triggered
    assert rebuilt.embeddings.shape == (4, EMBEDDING_SIZE)
