"""A dataset's own config.json, and calibration leaving out people in the dataset."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from face_pipeline.calibration import absent_strangers, normalise_name
from face_pipeline.index import IndexEntry
from face_pipeline.matching import config_path_for

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _config(path: Path, low: float, high: float) -> None:
    path.write_text(json.dumps({"threshold_low": low, "threshold_high": high}))


def test_config_path_prefers_the_datasets_own_file(tmp_path):
    dataset = tmp_path / "data" / "pool"
    dataset.mkdir(parents=True)
    assert config_path_for(dataset) == tmp_path / "data" / "config.json"

    _config(dataset / "config.json", 0.1, 0.2)
    assert config_path_for(dataset) == dataset / "config.json"


def test_cli_uses_the_datasets_own_thresholds(tmp_path):
    data = tmp_path / "data"
    dataset = data / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset)
    _config(data / "config.json", 2.0, 2.0)  # would label everything NO_MATCH
    _config(dataset / "config.json", -1.0, -1.0)  # labels everything HIGH_CONFIDENCE

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "match.py"),
         "--image", str(FIXTURES / "obama_query.jpg"), "--dataset", str(dataset),
         "--report-out", str(tmp_path / "report.html")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert lines and all(line.endswith("HIGH_CONFIDENCE") for line in lines)


def test_page_uses_the_datasets_own_thresholds(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    from face_pipeline.index import get_or_build_index

    data = tmp_path / "data"
    dataset = data / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset)
    get_or_build_index(dataset)
    _config(data / "config.json", 0.1, 0.2)
    _config(dataset / "config.json", 0.3, 0.6)
    monkeypatch.setenv("ALTEREGO_DATA_DIR", str(data))

    at = AppTest.from_file(str(REPO_ROOT / "app.py"), default_timeout=120)
    at.run()

    assert at.slider(key="thresholds::dataset").value == (0.3, 0.6)


@pytest.mark.parametrize("a, b", [
    ("Al_Pacino", "Al Pacino"),
    ("AL_PACINO", "al_pacino"),
    ("Pelé", "Pele"),
    ("Kimi_Räikkönen", "Kimi_Raikkonen"),
    # Found in the real pool: he counted as a stranger, inflating the threshold.
    ("George_W_Bush", "George_W._Bush"),
    ("Martin_Luther_King_Jr", "Martin Luther King, Jr."),
    ("Jean-Claude_Van_Damme", "Jean Claude Van Damme"),
])
def test_names_match_ignoring_case_accents_and_underscores(a, b):
    assert normalise_name(a) == normalise_name(b)


def test_different_names_stay_different():
    assert normalise_name("Al_Pacino") != normalise_name("Al_Gore")


def test_people_in_the_dataset_are_not_strangers():
    by_person = {"Al_Pacino": [np.array([1.0, 0.0])], "Nobody_Else": [np.array([0.0, 1.0]), np.array([0.5, 0.5])]}
    entries = [IndexEntry(person="Al Pacino", filepath="a.jpg"), IndexEntry(person="Someone", filepath="b.jpg")]

    strangers, removed = absent_strangers(by_person, entries)

    assert removed == ["Al_Pacino"]
    assert strangers.tolist() == [[0.0, 1.0], [0.5, 0.5]]


def test_disjoint_dataset_keeps_every_stranger_in_order():
    by_person = {"A": [np.array([1.0, 0.0])], "B": [np.array([0.0, 1.0])]}

    strangers, removed = absent_strangers(by_person, [IndexEntry(person="C", filepath="c.jpg")])

    assert removed == []
    assert strangers.tolist() == [[1.0, 0.0], [0.0, 1.0]]


def _calibrated(tmp_path, name, extra_person=None):
    dataset = tmp_path / name
    shutil.copytree(FIXTURES / "dataset", dataset)
    (dataset / ".matchcache").exists() and shutil.rmtree(dataset / ".matchcache", ignore_errors=True)
    if extra_person:
        folder = dataset / extra_person
        folder.mkdir()
        first = sorted((FIXTURES / "calibration" / extra_person).glob("*.jpg"))[0]
        shutil.copy(first, folder / first.name)
    out = tmp_path / f"{name}.json"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "calibrate.py"),
         "--calibration-dir", str(FIXTURES / "calibration"),
         "--dataset", str(dataset), "--config-out", str(out)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(out.read_text()), result.stdout


def test_overlap_does_not_change_the_low_threshold_and_is_reported(tmp_path):
    plain, _ = _calibrated(tmp_path, "plain")
    overlapping, stdout = _calibrated(tmp_path, "overlapping", extra_person="Kit_Harington")

    assert overlapping["threshold_low"] == plain["threshold_low"]
    assert "1 calibration" in stdout


def test_overlapping_person_does_not_inflate_the_high_threshold(tmp_path):
    # Kit_Harington's own photo would score ~1.0 if he counted as a stranger.
    overlapping, _ = _calibrated(tmp_path, "overlapping", extra_person="Kit_Harington")
    assert overlapping["threshold_high"] < 0.9
