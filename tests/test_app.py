"""Headless tests of the web UI (app.py) with Streamlit's AppTest.

Skipped when Streamlit is not installed (it is a UI-only dependency, see
requirements-ui.txt).
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from face_pipeline.index import get_or_build_index  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
APP = REPO_ROOT / "app.py"
QUERY = FIXTURES / "obama_query.jpg"
CARD_LINE = re.compile(r"`(-?\d+\.\d{4})` :\w+\[\*\*(\w+)\*\*\]")


def _write_config(data_dir: Path, low: float, high: float) -> Path:
    config = data_dir / "config.json"
    config.write_text(json.dumps({"threshold_low": low, "threshold_high": high}))
    return config


def _twelve_faces(dataset_dir: Path, first_person: str = "Person_00") -> None:
    # 12 faces in 12 person folders, as in test_match_cli.py: 9 distinct
    # fixture images plus mirrored copies of 3 of them.
    distinct = [
        FIXTURES / "biden_1.jpg",
        FIXTURES / "obama_1.jpg",
        FIXTURES / "obama_2.jpg",
        FIXTURES / "obama_query.jpg",
        FIXTURES / "pk_sunglasses_shirt.jpg",
        *sorted((FIXTURES / "calibration").glob("*/*.jpg")),
    ]
    images = [cv2.imread(str(p)) for p in distinct]
    images += [cv2.flip(img, 1) for img in images[:3]]
    for i, image in enumerate(images):
        person = first_person if i == 0 else f"Person_{i:02d}"
        person_dir = dataset_dir / person
        person_dir.mkdir(parents=True)
        cv2.imwrite(str(person_dir / "face.jpg"), image)


@pytest.fixture(scope="module")
def indexed_data_dir(tmp_path_factory):
    """data/ with one indexed dataset (twelve), one unindexed folder and results/."""
    data_dir = tmp_path_factory.mktemp("app") / "data"
    _twelve_faces(data_dir / "twelve")
    get_or_build_index(data_dir / "twelve")
    shutil.copytree(FIXTURES / "dataset", data_dir / "unindexed")
    shutil.rmtree(data_dir / "unindexed" / ".matchcache")
    (data_dir / "results").mkdir()
    _write_config(data_dir, 0.2, 0.4)
    return data_dir


def _app(data_dir: Path, monkeypatch) -> AppTest:
    monkeypatch.setenv("ALTEREGO_DATA_DIR", str(data_dir))
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    return at


def _upload(at: AppTest, content: bytes, name: str = "query.jpg") -> AppTest:
    at.file_uploader[0].upload(name, content, "image/jpeg").run()
    return at


def _cards(at: AppTest):
    """(person, score, label) per result card, in page order."""
    names = [t.value.split(" ", 1)[1] for t in at.text if t.value.startswith("#")]
    lines = [CARD_LINE.fullmatch(m.value) for m in at.markdown]
    scores_labels = [(float(m.group(1)), m.group(2)) for m in lines if m]
    assert len(names) == len(scores_labels)
    return [(n, s, lbl) for n, (s, lbl) in zip(names, scores_labels)]


# --- 3.1 dataset selection ---------------------------------------------------


def test_lists_only_indexed_datasets(indexed_data_dir, monkeypatch):
    at = _app(indexed_data_dir, monkeypatch)
    assert not at.exception
    assert at.selectbox(key="dataset").options == ["twelve"]


def test_no_indexed_dataset_tells_user_to_index_one(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    shutil.copytree(FIXTURES / "dataset", data_dir / "unindexed")
    shutil.rmtree(data_dir / "unindexed" / ".matchcache")

    at = _app(data_dir, monkeypatch)

    assert not at.exception
    assert any("match.py" in i.value for i in at.info)
    assert len(at.file_uploader) == 0


def test_switching_dataset_keeps_the_uploaded_photo(indexed_data_dir, tmp_path, monkeypatch):
    # "with_me" is "twelve" plus a person "Me" holding a copy of the query
    # photo, as data/celebrities_plus_me is data/celebrities plus the user.
    data_dir = tmp_path / "data"
    shutil.copytree(indexed_data_dir, data_dir)
    shutil.copytree(data_dir / "twelve", data_dir / "with_me")
    (data_dir / "with_me" / "Me").mkdir()
    shutil.copy(QUERY, data_dir / "with_me" / "Me" / "me.jpg")
    get_or_build_index(data_dir / "with_me")

    at = _upload(_app(data_dir, monkeypatch), QUERY.read_bytes())
    assert "Me" not in [name for name, _, _ in _cards(at)]

    at.selectbox(key="dataset").select("with_me").run()

    assert _cards(at)[0][0] == "Me"


# --- 3.2 thresholds ----------------------------------------------------------


def test_thresholds_preset_from_config_without_notice(indexed_data_dir, monkeypatch):
    at = _app(indexed_data_dir, monkeypatch)
    assert at.slider(key="thresholds::twelve").value == (0.2, 0.4)
    assert len(at.warning) == 0


def test_moving_thresholds_relabels_and_shows_notice(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())

    at.slider(key="thresholds::twelve").set_value((0.0, 0.0)).run()

    assert {label for _, _, label in _cards(at)} <= {"HIGH_CONFIDENCE", "NO_MATCH"}
    assert any(label == "HIGH_CONFIDENCE" for _, _, label in _cards(at))
    assert any("calibrated" in w.value for w in at.warning)


def test_missing_config_shows_calibrate_error(indexed_data_dir, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    shutil.copytree(indexed_data_dir, data_dir)
    (data_dir / "config.json").unlink()

    at = _app(data_dir, monkeypatch)

    assert any("calibrate.py" in e.value for e in at.error)
    assert len(at.file_uploader) == 0


# --- 3.3 upload and result cards ----------------------------------------------


def test_ten_cards_matching_the_cli(indexed_data_dir, monkeypatch, tmp_path):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    cards = _cards(at)

    cli = subprocess.run(
        [
            sys.executable, str(REPO_ROOT / "match.py"),
            "--image", str(QUERY),
            "--dataset", str(indexed_data_dir / "twelve"),
            "--report-out", str(tmp_path / "cli_report.html"),
        ],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert cli.returncode == 0, cli.stderr
    cli_lines = cli.stdout.strip().splitlines()

    assert len(cards) == 10
    assert [f"{n}: {s:.4f} {lbl}" for n, s, lbl in cards] == cli_lines


def test_candidates_shown_control(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    at.slider(key="top").set_value(3).run()
    assert len(_cards(at)) == 3


def test_face_crop_shown_next_to_photo(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    captions = [img.proto.imgs[0].caption for img in at.image]
    assert captions[:2] == ["Your photo", "Face used for matching"]
    # The photo, the crop, then one image per card.
    assert len(at.image) == 2 + 10


def test_no_face_shows_error_and_nothing_else(indexed_data_dir, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    shutil.copytree(indexed_data_dir, data_dir)
    (data_dir / "results" / "summary.html").unlink(missing_ok=True)

    at = _upload(
        _app(data_dir, monkeypatch), (REPO_ROOT / "data" / "demo" / "no_face.jpg").read_bytes()
    )

    assert any(e.value == "No face detected" for e in at.error)
    assert _cards(at) == []
    assert len(at.get("download_button")) == 0
    assert not (data_dir / "results" / "summary.html").exists()


def test_unreadable_file_shows_error(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), b"this is not an image")
    assert any("could not be read" in e.value for e in at.error)
    assert _cards(at) == []


def test_person_names_are_shown_as_plain_text(tmp_path, monkeypatch):
    # Folder names are untrusted (HW6 review 1). Windows forbids < > * in
    # folder names, so this one uses Markdown and HTML-entity syntax instead.
    name = "_italic_ [x](y) &amp;"
    data_dir = tmp_path / "data"
    _twelve_faces(data_dir / "evil", first_person=name)
    get_or_build_index(data_dir / "evil")
    _write_config(data_dir, 0.0, 0.0)

    at = _upload(_app(data_dir, monkeypatch), (FIXTURES / "biden_1.jpg").read_bytes())

    assert _cards(at)[0][0] == name
    assert not any(name in m.value for m in at.markdown)


# --- 3.4 report ----------------------------------------------------------------


def test_report_written_offered_and_follows_thresholds(indexed_data_dir, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    shutil.copytree(indexed_data_dir, data_dir)
    report = data_dir / "results" / "summary.html"
    report.unlink(missing_ok=True)

    at = _upload(_app(data_dir, monkeypatch), QUERY.read_bytes())

    assert len(at.get("download_button")) == 1
    html = report.read_text(encoding="utf-8")
    assert "data:image/jpeg;base64," in html
    assert 'src="http' not in html
    for _, _, label in _cards(at):
        assert label in html

    at.slider(key="thresholds::twelve").set_value((1.0, 1.0)).run()

    html = report.read_text(encoding="utf-8")
    assert "HIGH_CONFIDENCE" not in html
    assert "LOW_CONFIDENCE" not in html
    assert "NO_MATCH" in html
