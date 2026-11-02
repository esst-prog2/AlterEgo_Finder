"""Tests for setup_data.py, using a tiny archive built from fixtures (no network, no LFW)."""

import collections
import hashlib
import io
import json
import os
import shutil
import tarfile
from pathlib import Path

import pytest

import calibrate
import setup_data

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    """A small LFW-like archive, a split list naming part of it, and a data dir."""
    images = {
        "Cand_A/Cand_A_0001.jpg": FIXTURES / "obama_1.jpg",
        "Cand_B/Cand_B_0001.jpg": FIXTURES / "biden_1.jpg",
        "Unlisted/Unlisted_0001.jpg": FIXTURES / "obama_2.jpg",
    }
    calibration = sorted((FIXTURES / "calibration").glob("*/*.jpg"))
    for path in calibration:
        images[f"Cal_{path.parent.name}/{path.name}"] = path

    archive = tmp_path / "tiny.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        for rel, source in images.items():
            tar.add(source, arcname=f"lfw/{rel}")

    split = tmp_path / "split.json"
    split.write_text(json.dumps({
        "celebrities": ["Cand_A/Cand_A_0001.jpg", "Cand_B/Cand_B_0001.jpg"],
        "calibration": [rel for rel in images if rel.startswith("Cal_")],
    }))
    monkeypatch.setattr(setup_data, "LFW_SHA256", hashlib.sha256(archive.read_bytes()).hexdigest())

    class Tiny:
        pass

    t = Tiny()
    t.archive, t.split, t.images, t.data = archive, split, images, tmp_path / "data"
    t.args = ["--data-dir", str(t.data), "--split", str(split)]
    return t


def _forbid_download(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("must not download")

    monkeypatch.setattr(setup_data.urllib.request, "urlopen", fail)


def _count_calibrations(monkeypatch):
    calls = []
    real = calibrate.main

    def spy(argv=None):
        calls.append(argv)
        return real(argv)

    monkeypatch.setattr(setup_data.calibrate, "main", spy)
    return calls


def test_builds_listed_images_byte_identical_and_only_those(tiny, monkeypatch):
    _forbid_download(monkeypatch)

    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0

    for rel in ("Cand_A/Cand_A_0001.jpg", "Cand_B/Cand_B_0001.jpg"):
        assert (tiny.data / "celebrities" / rel).read_bytes() == tiny.images[rel].read_bytes()
    for rel, source in tiny.images.items():
        if rel.startswith("Cal_"):
            assert (tiny.data / "calibration" / rel).read_bytes() == source.read_bytes()
    assert not list(tiny.data.rglob("Unlisted*"))


def test_full_run_writes_thresholds_and_index(tiny):
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0

    config = json.loads((tiny.data / "config.json").read_text())
    assert {"threshold_low", "threshold_high"} <= set(config)
    assert (tiny.data / "celebrities" / ".matchcache" / "embeddings.npy").exists()


def test_checksum_mismatch_builds_nothing(tiny, monkeypatch, capsys):
    monkeypatch.setattr(setup_data, "LFW_SHA256", "0" * 64)

    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 1

    assert "checksum" in capsys.readouterr().err.lower()
    assert not (tiny.data / "celebrities").exists()
    assert not (tiny.data / "config.json").exists()


def test_image_missing_from_archive_is_named(tiny, capsys):
    split = json.loads(tiny.split.read_text())
    split["celebrities"].append("Nobody/Nobody_0001.jpg")
    tiny.split.write_text(json.dumps(split))

    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 1

    assert "Nobody/Nobody_0001.jpg" in capsys.readouterr().err
    assert not (tiny.data / "config.json").exists()


def test_second_run_neither_downloads_nor_recalibrates(tiny, monkeypatch):
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0
    config_before = (tiny.data / "config.json").read_bytes()
    _forbid_download(monkeypatch)
    calls = _count_calibrations(monkeypatch)

    assert setup_data.main(tiny.args) == 0

    assert calls == []
    assert (tiny.data / "config.json").read_bytes() == config_before


def test_recalibrate_option_recalibrates(tiny, monkeypatch):
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0
    calls = _count_calibrations(monkeypatch)

    assert setup_data.main([*tiny.args, "--recalibrate"]) == 0

    assert len(calls) == 1


def test_run_after_an_interruption_finishes_the_job(tiny):
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0
    (tiny.data / "celebrities" / "Cand_B" / "Cand_B_0001.jpg").unlink()
    (tiny.data / "config.json").unlink()

    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0

    assert (tiny.data / "celebrities" / "Cand_B" / "Cand_B_0001.jpg").exists()
    assert (tiny.data / "config.json").exists()


def test_missing_index_is_rebuilt_without_recalibrating(tiny, monkeypatch):
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0
    shutil.rmtree(tiny.data / "celebrities" / ".matchcache")
    calls = _count_calibrations(monkeypatch)

    assert setup_data.main(tiny.args) == 0

    assert calls == []
    assert (tiny.data / "celebrities" / ".matchcache" / "embeddings.npy").exists()


def test_other_folders_are_untouched(tiny):
    mine = tiny.data / "my_photo" / "me.jpg"
    mine.parent.mkdir(parents=True)
    mine.write_bytes(b"my own photo")
    stamp = mine.stat().st_mtime_ns

    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0

    assert mine.read_bytes() == b"my own photo"
    assert mine.stat().st_mtime_ns == stamp


def test_download_verifies_and_keeps_the_archive(tiny, monkeypatch):
    body = tiny.archive.read_bytes()
    monkeypatch.setattr(setup_data.urllib.request, "urlopen",
                        lambda url, timeout: _Response(body))

    assert setup_data.main(tiny.args) == 0

    assert (tiny.data / "lfw" / "lfw.tgz").read_bytes() == body
    assert not (tiny.data / "lfw" / "lfw.tgz.part").exists()


def test_corrupt_download_leaves_no_archive(tiny, monkeypatch, capsys):
    monkeypatch.setattr(setup_data.urllib.request, "urlopen",
                        lambda url, timeout: _Response(b"not the archive"))

    assert setup_data.main(tiny.args) == 1

    assert "checksum" in capsys.readouterr().err.lower()
    assert not (tiny.data / "lfw" / "lfw.tgz").exists()
    assert not (tiny.data / "lfw" / "lfw.tgz.part").exists()


def test_failed_download_says_how_to_retry_and_leaves_no_file(tiny, monkeypatch, capsys):
    def stalled(url, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr(setup_data.urllib.request, "urlopen", stalled)

    assert setup_data.main(tiny.args) == 1

    err = capsys.readouterr().err
    assert "--tarball" in err and "again" in err
    assert not (tiny.data / "lfw" / "lfw.tgz").exists()
    assert not (tiny.data / "lfw" / "lfw.tgz.part").exists()


def test_committed_split_list_is_the_documented_dataset():
    split = json.loads((REPO_ROOT / "data" / "lfw_split.json").read_text(encoding="utf-8"))
    people = {key: [rel.split("/")[0] for rel in rels] for key, rels in split.items()}

    assert len(split["celebrities"]) == 500
    assert len(set(people["celebrities"])) == 500  # one image each
    assert len(set(people["calibration"])) == 200
    assert max(people["calibration"].count(p) for p in set(people["calibration"])) <= 4
    assert not set(people["celebrities"]) & set(people["calibration"])
    for rels in split.values():
        assert all(rel.endswith(".jpg") and ".." not in rel for rel in rels)


class _Response(io.BytesIO):
    """Stands in for urlopen's response: a readable body with a length header."""

    def __init__(self, body: bytes):
        super().__init__(body)
        self.headers = {"Content-Length": str(len(body))}


# --- optional public-figure pool ------------------------------------------------


@pytest.fixture
def fake_build(tiny, monkeypatch):
    """Stands in for wikidata_pool.build_pool: `limit` copies of fixture faces."""
    people_file = tiny.split.parent / "people.json"
    people_file.write_text(json.dumps([{"qid": "Q1", "folder": "P"}]))
    calls = []

    def build(people, pool_dir, limit):
        calls.append((people, pool_dir, limit))
        have = sorted(pool_dir.glob("*/*.jpg")) if pool_dir.exists() else []
        sources = [FIXTURES / "obama_1.jpg", FIXTURES / "biden_1.jpg", FIXTURES / "obama_2.jpg"]
        for i in range(len(have), min(limit, len(sources))):
            (pool_dir / f"P{i}").mkdir(parents=True, exist_ok=True)
            shutil.copy(sources[i], pool_dir / f"P{i}" / f"P{i}_0001.jpg")
        saved = max(0, min(limit, len(sources)) - len(have))
        if saved:  # like the real build, which writes this only when something changed
            (pool_dir / "attribution.json").write_text("{}")
        return collections.Counter(saved=saved)

    monkeypatch.setattr(setup_data, "build_pool", build)
    tiny.pool_args = [*tiny.args, "--tarball", str(tiny.archive), "--wikidata", "--people", str(people_file)]
    tiny.build_calls = calls
    return tiny


def test_basic_setup_does_not_touch_the_pool(tiny, monkeypatch):
    monkeypatch.setattr(setup_data, "build_pool", lambda *a, **k: pytest.fail("must not build the pool"))
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0
    assert not (tiny.data / "wikidata").exists()


def test_pool_gets_its_own_thresholds_and_index_and_leaves_the_others(fake_build):
    tiny = fake_build
    assert setup_data.main([*tiny.args, "--tarball", str(tiny.archive)]) == 0
    base_config = (tiny.data / "config.json").read_bytes()

    assert setup_data.main([*tiny.pool_args, "--wikidata-limit", "2"]) == 0

    assert tiny.build_calls[-1][2] == 2
    own = json.loads((tiny.data / "wikidata" / "config.json").read_text())
    assert {"threshold_low", "threshold_high"} <= set(own)
    assert (tiny.data / "wikidata" / ".matchcache" / "embeddings.npy").exists()
    assert (tiny.data / "config.json").read_bytes() == base_config


def test_default_pool_size_is_500(fake_build):
    setup_data.main(fake_build.pool_args)
    assert fake_build.build_calls[-1][2] == 500


def test_pool_recalibrates_only_when_it_changed(fake_build, monkeypatch):
    tiny = fake_build
    assert setup_data.main([*tiny.pool_args, "--wikidata-limit", "2"]) == 0
    calls = _count_calibrations(monkeypatch)
    pool_config = tiny.data / "wikidata" / "config.json"

    assert setup_data.main([*tiny.pool_args, "--wikidata-limit", "2"]) == 0
    assert calls == []

    # Grown, so the threshold fitted to the old size no longer holds.
    os.utime(pool_config, (1, 1))
    assert setup_data.main([*tiny.pool_args, "--wikidata-limit", "3"]) == 0
    assert len(calls) == 1
    assert "wikidata" in calls[0][calls[0].index("--dataset") + 1]


def test_pool_failure_reports_resume_and_exits_1(fake_build, monkeypatch, capsys):
    def stopped(*a, **k):
        raise setup_data.PoolError("rate limited: run the same command again later")

    monkeypatch.setattr(setup_data, "build_pool", stopped)

    assert setup_data.main(fake_build.pool_args) == 1

    assert "again" in capsys.readouterr().err
    assert not (fake_build.data / "wikidata" / "config.json").exists()


def test_committed_people_list_is_usable():
    people = json.loads((REPO_ROOT / "data" / "wikidata_people.json").read_text(encoding="utf-8"))

    assert len(people) >= 500
    assert len({p["qid"] for p in people}) == len(people)
    assert len({p["folder"] for p in people}) == len(people)
    assert all(p["folder"].isascii() and "/" not in p["folder"] and ".." not in p["folder"] for p in people)
