import re
from pathlib import Path

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
