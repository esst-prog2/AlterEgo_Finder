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
# A card's score line, e.g. "`0.2146` :orange[**Alter Ego**]". The page shows
# only the plain names; tests map them back to the CLI's technical labels.
CARD_LINE = re.compile(r"`(-?\d+\.\d{4})` :\w+\[\*\*(.+?)\*\*\]")
PLAIN_NAMES = {"HIGH_CONFIDENCE": "Same person", "LOW_CONFIDENCE": "Alter Ego",
               "NO_MATCH": "Not You"}
LABEL_OF = {plain: label for label, plain in PLAIN_NAMES.items()}
TECHNICAL = ("HIGH_CONFIDENCE", "LOW_CONFIDENCE", "NO_MATCH")


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
    """(person, score, technical label) per result card, in page order."""
    names = [t.value.split(" ", 1)[1] for t in at.text if t.value.startswith("#")]
    lines = [CARD_LINE.fullmatch(m.value) for m in at.markdown]
    scores_labels = [(float(m.group(1)), LABEL_OF[m.group(2)]) for m in lines if m]
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


# --- similarity target ---------------------------------------------------------


def _target_faces(at: AppTest):
    """The face points in the similarity target's spec, or None if no target."""
    charts = at.get("vega_lite_chart")
    if not charts:
        return None
    spec = json.loads(charts[0].proto.spec)
    return spec, [
        row
        for layer in spec["layer"]
        for row in layer.get("data", {}).get("values", [])
        if "score" in row
    ]


def test_target_places_every_face_at_exactly_one_minus_score(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())

    target = _target_faces(at)
    assert target is not None
    _, faces = target
    assert len(faces) == 12
    for row in faces:
        assert (row["x"] ** 2 + row["y"] ** 2) ** 0.5 == pytest.approx(1 - row["score"])
    assert sum(row["named"] for row in faces) == 10


def test_target_rings_follow_the_threshold_slider(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    spec_text = at.get("vega_lite_chart")[0].proto.spec
    assert "high 0.4000" in spec_text and "low 0.2000" in spec_text

    at.slider(key="thresholds::twelve").set_value((0.0, 0.0)).run()

    spec_text = at.get("vega_lite_chart")[0].proto.spec
    assert "high 0.0000" in spec_text and "low 0.0000" in spec_text


def test_no_target_on_error_pages(indexed_data_dir, monkeypatch):
    at = _upload(
        _app(indexed_data_dir, monkeypatch), (REPO_ROOT / "data" / "demo" / "no_face.jpg").read_bytes()
    )
    assert _target_faces(at) is None

    at = _upload(_app(indexed_data_dir, monkeypatch), b"this is not an image")
    assert _target_faces(at) is None


def test_target_labels_rays_and_centre_for_slides(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    spec, faces = _target_faces(at)
    texts = [row.get("text", "") for layer in spec["layer"] for row in layer["data"]["values"]]

    # Named faces are labelled "#rank Name"; only #1 also shows its score.
    for row in faces:
        if row["named"]:
            expected = f"#{row['rank']} {row['person']}"
            if row["rank"] == 1:
                expected += f" ({row['score']:.4f})"
            assert expected in texts
    # The centre is labelled "You", and the top 5 get guide rays from it.
    assert any(layer["mark"].get("text") == "You" for layer in spec["layer"])
    rays = [layer for layer in spec["layer"] if layer["mark"]["type"] == "rule"]
    assert len(rays) == 1 and len(rays[0]["data"]["values"]) == 5
    # Streamlit's renderer drew nothing at all when the rays used a "datum"
    # encoding for the centre (2026-10-20); every position must be a data field.
    assert '"datum"' not in json.dumps(spec)


def test_target_text_follows_the_light_or_dark_theme():
    # The page's theme decides the colour of the centre, names and ring labels,
    # so they stay readable on Streamlit's dark background (2026-10-20).
    sys.path.insert(0, str(REPO_ROOT))
    from app import _target_spec
    from face_pipeline.index import IndexEntry

    labeled = [(IndexEntry(person=f"P{i}", filepath="p.jpg"), 0.5 - i / 10, "LOW_CONFIDENCE")
               for i in range(5)]

    def text_colours(theme):
        spec = _target_spec(labeled, 3, 0.2, 0.4, theme=theme)
        return {layer["mark"].get("color") for layer in spec["layer"]
                if layer["mark"]["type"] in ("text", "point")}

    assert text_colours("light") == {"#1f2328", "#57606a"}
    assert text_colours("dark") == {"#f0f6fc", "#9198a1"}
    assert text_colours(None) == {"#8c959f"}


def test_target_labels_do_not_sit_on_named_faces():
    # Screenshots 2026-10-20: ring labels on the rings collided with named
    # faces, and centred names ran into each other.
    sys.path.insert(0, str(REPO_ROOT))
    from app import _target_spec
    from face_pipeline.index import IndexEntry

    labeled = [(IndexEntry(person=f"P{i}", filepath="p.jpg"), 0.5 - i / 30, "LOW_CONFIDENCE")
               for i in range(14)]
    spec = _target_spec(labeled, 10, 0.2, 0.4, theme="dark")
    layers = spec["layer"]
    reach = max((r["x"] ** 2 + r["y"] ** 2) ** 0.5 for l in layers
                for r in l["data"]["values"] if "score" in r)

    # The ring legend sits in a corner, outside every face and ring.
    # Legend lines: fixed text, left-aligned, no offset (names have a dx).
    legend = [l for l in layers if l["mark"]["type"] == "text" and "text" in l["mark"]
              and l["mark"].get("align") == "left" and "dx" not in l["mark"]]
    assert [l["mark"]["text"] for l in legend] == [
        "inside inner ring (high 0.4000): Same person",
        "between rings (low 0.2000): Alter Ego",
        "outside: Not You",
    ]
    for l in legend:
        (row,) = l["data"]["values"]
        assert row["y"] > max(reach, 1 - 0.2)

    # Names sit beside their dot, pointing outward: left-aligned on the right half.
    name_layers = [l for l in layers if l["mark"]["type"] == "text" and "dx" in l["mark"]]
    for l in name_layers:
        for row in l["data"]["values"]:
            assert (row["x"] >= 0) == (l["mark"]["align"] == "left")
    assert sum(len(l["data"]["values"]) for l in name_layers) == 10



def test_target_tooltips_show_thumbnails_for_named_faces_only(indexed_data_dir, monkeypatch):
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    spec, faces = _target_faces(at)

    named = [r for r in faces if r["named"]]
    others = [r for r in faces if not r["named"]]
    assert named and others
    assert all(r["image"].startswith("data:image/jpeg;base64,") for r in named)
    # Thumbnails are 128 px on their longest side (64 px was too small to see).
    import base64
    import numpy as np
    for r in named:
        raw = base64.b64decode(r["image"].split(",", 1)[1])
        thumb = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        assert max(thumb.shape[:2]) == 128
    assert all("image" not in r for r in others)
    # vega-tooltip renders a field titled "image" as a picture.
    named_layer = next(l for l in spec["layer"]
                       if l["data"]["values"] and l["data"]["values"][0].get("named") is True
                       and l["mark"]["type"] == "circle")
    assert {"field": "image", "title": "image"} in named_layer["encoding"]["tooltip"]



def test_page_never_shows_the_technical_label_names(indexed_data_dir, monkeypatch):
    # The page uses plain names only; HIGH_CONFIDENCE etc. are for developers
    # (CLI, report, specs) - decided 2026-10-20.
    at = _upload(_app(indexed_data_dir, monkeypatch), QUERY.read_bytes())
    at.slider(key="thresholds::twelve").set_value((0.0, 0.3)).run()  # some of each band

    shown = [e.value for kind in (at.markdown, at.text, at.caption, at.warning, at.info,
                                  at.error, at.subheader, at.title) for e in kind]
    shown += [s.proto.help for s in at.slider]
    shown += [c.proto.spec for c in at.get("vega_lite_chart")]
    page = "\n".join(shown)
    assert {label for _, _, label in _cards(at)} >= {"HIGH_CONFIDENCE", "LOW_CONFIDENCE"}
    for name in TECHNICAL:
        assert name not in page


def test_card_images_are_cropped_to_squares():
    sys.path.insert(0, str(REPO_ROOT))
    import numpy as np
    from app import _square_crop

    wide = np.zeros((100, 160, 3), dtype=np.uint8)
    wide[:, 30:130] = 255  # the centre 100x100 is white
    tall = np.zeros((90, 40, 3), dtype=np.uint8)
    assert _square_crop(wide).shape == (100, 100, 3)
    assert _square_crop(wide).min() == 255  # centred crop
    assert _square_crop(tall).shape == (40, 40, 3)
