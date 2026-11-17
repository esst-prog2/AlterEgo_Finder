import re
from pathlib import Path

from face_pipeline.images import read_image
from face_pipeline.index import IndexEntry
from face_pipeline.report import REPORT_TOP_K, render_report

FIXTURES = Path(__file__).parent / "fixtures"
QUERY_IMAGE = FIXTURES / "obama_query.jpg"


def _fake_results(n: int):
    results = []
    for i in range(n):
        entry = IndexEntry(person=f"Person_{i}", filepath=QUERY_IMAGE)
        score = 1.0 - i * 0.01
        label = "HIGH_CONFIDENCE" if i == 0 else "NO_MATCH"
        results.append((entry, score, label))
    return results


def test_render_report_embeds_images_and_labels(tmp_path):
    output_path = tmp_path / "report.html"
    results = [
        (IndexEntry(person="Barack_Obama", filepath=FIXTURES / "obama_1.jpg"), 0.80, "HIGH_CONFIDENCE"),
        (IndexEntry(person="Joe_Biden", filepath=FIXTURES / "biden_1.jpg"), -0.07, "NO_MATCH"),
    ]

    render_report(QUERY_IMAGE, results, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "data:image/jpeg;base64," in content
    assert "Barack_Obama" in content
    assert "Joe_Biden" in content
    assert "HIGH_CONFIDENCE" in content
    assert "NO_MATCH" in content


def test_render_report_caps_at_top_k(tmp_path):
    output_path = tmp_path / "report.html"
    results = _fake_results(REPORT_TOP_K + 5)

    render_report(QUERY_IMAGE, results, output_path)

    content = output_path.read_text(encoding="utf-8")
    included = sum(1 for i in range(REPORT_TOP_K + 5) if f"Person_{i}" in content)
    assert included == REPORT_TOP_K
    # Specifically the top-ranked ones, not an arbitrary subset.
    for i in range(REPORT_TOP_K):
        assert f"Person_{i}" in content
    for i in range(REPORT_TOP_K, REPORT_TOP_K + 5):
        assert f"Person_{i}" not in content


def test_render_report_is_self_contained(tmp_path):
    output_path = tmp_path / "report.html"
    results = [
        (IndexEntry(person="Barack_Obama", filepath=FIXTURES / "obama_1.jpg"), 0.80, "HIGH_CONFIDENCE"),
    ]

    render_report(QUERY_IMAGE, results, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "<link" not in content
    assert "<script src=" not in content
    # Every img src must be a data: URI, never a file path or external URL.
    img_srcs = re.findall(r'<img src="([^"]*)"', content)
    assert img_srcs, "expected at least one <img> tag"
    assert all(src.startswith("data:image/") for src in img_srcs)


def test_render_report_escapes_person_names(tmp_path):
    # Person names come from dataset folder names, which the user doesn't
    # control (e.g. a downloaded dataset). They must not become markup.
    output_path = tmp_path / "report.html"
    hostile = '"><img src=x onerror=alert(1)>'
    results = [(IndexEntry(person=hostile, filepath=FIXTURES / "obama_1.jpg"), 0.80, "HIGH_CONFIDENCE")]

    render_report(QUERY_IMAGE, results, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "onerror=alert(1)>" not in content
    assert "&quot;&gt;&lt;img src=x onerror=alert(1)&gt;" in content


def test_render_report_accepts_query_as_image_array(tmp_path):
    # The web UI passes the decoded upload, never saving it as its own file.
    import cv2

    results = _fake_results(2)
    from_path = tmp_path / "from_path.html"
    from_array = tmp_path / "from_array.html"

    render_report(QUERY_IMAGE, results, from_path)
    render_report(read_image(QUERY_IMAGE), results, from_array)

    assert from_array.read_text(encoding="utf-8") == from_path.read_text(encoding="utf-8")


# --- shared design (apply-shared-design) -------------------------------------

def _three_labels_report(tmp_path, attribution=None):
    output_path = tmp_path / "report.html"
    results = [
        (IndexEntry(person="Barack_Obama", filepath=FIXTURES / "obama_1.jpg"), 0.80, "HIGH_CONFIDENCE"),
        (IndexEntry(person="Joe_Biden", filepath=FIXTURES / "biden_1.jpg"), 0.25, "LOW_CONFIDENCE"),
        (IndexEntry(person="Someone", filepath=FIXTURES / "biden_1.jpg"), 0.05, "NO_MATCH"),
    ]
    render_report(QUERY_IMAGE, results, output_path, attribution=attribution)
    return output_path.read_text(encoding="utf-8")


def test_report_header_carries_the_logo_inline(tmp_path):
    content = _three_labels_report(tmp_path)
    header = re.search(r"<header>(.*?)</header>", content, re.S).group(1)
    # The logo is the target in miniature, inline SVG: both rings and the navy cross.
    assert '<svg class="mark"' in header
    for colour in ("#d4a72c", "#1a7f37", "#1d3c78"):
        assert colour in header
    assert "AlterEgo Finder" in header


def test_each_classification_has_its_shared_dot_colour(tmp_path):
    content = _three_labels_report(tmp_path)
    dots = re.findall(r'<span class="dot" style="background: (#[0-9a-f]{6})"></span>(\w+)</div>', content)
    assert dots == [("#1a7f37", "HIGH_CONFIDENCE"), ("#d4a72c", "LOW_CONFIDENCE"), ("#8c959f", "NO_MATCH")]


def test_report_loads_nothing_from_the_network(tmp_path):
    source = "https://commons.wikimedia.org/wiki/File:Barack_Obama.jpg"
    attribution = {"fixtures/obama_1.jpg": {"author": "A", "license": "CC0", "source": source}}
    content = _three_labels_report(tmp_path, attribution)
    # Fonts are embedded; the only URLs are the credits' source links and the SVG namespace.
    assert "data:font/woff2;base64," in content
    urls = set(re.findall(r"https?://[^\s\"')<>]+", content))
    assert urls <= {source, "http://www.w3.org/2000/svg"}, urls
