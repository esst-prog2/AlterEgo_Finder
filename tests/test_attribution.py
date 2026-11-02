"""Photo credits: reading them, and showing them in the report and on the CLI's report."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from face_pipeline.attribution import credit_for, load_attribution, safe_source_url
from face_pipeline.index import IndexEntry
from face_pipeline.report import render_report

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
QUERY = FIXTURES / "obama_query.jpg"
SOURCE = "https://commons.wikimedia.org/wiki/File:A.jpg"


def _write(dataset: Path, images: dict) -> None:
    dataset.mkdir(parents=True, exist_ok=True)
    (dataset / "attribution.json").write_text(json.dumps({"images": images, "skipped": {}}), encoding="utf-8")


def test_no_file_means_no_attribution(tmp_path):
    assert load_attribution(tmp_path) == {}


def test_broken_file_means_no_attribution(tmp_path):
    (tmp_path / "attribution.json").write_text("{not json")
    assert load_attribution(tmp_path) == {}


def test_credit_found_by_person_and_file(tmp_path):
    entry = {"author": "Jane", "license": "CC BY 4.0", "source": SOURCE}
    _write(tmp_path, {"P/P_0001.jpg": entry})
    credits = load_attribution(tmp_path)

    assert credit_for(credits, tmp_path / "P" / "P_0001.jpg") == entry
    assert credit_for(credits, tmp_path / "Q" / "Q_0001.jpg") is None


def test_only_commons_pages_are_links():
    assert safe_source_url(SOURCE) == SOURCE
    assert safe_source_url("https://evil.example/") is None
    assert safe_source_url("javascript:alert(1)") is None
    assert safe_source_url("http://commons.wikimedia.org/wiki/File:A.jpg") is None
    assert safe_source_url("") is None
    assert safe_source_url('https://commons.wikimedia.org/wiki/"><script>') is None


def _report(tmp_path, credits):
    results = [(IndexEntry(person="P", filepath=FIXTURES / "obama_1.jpg"), 0.5, "LOW_CONFIDENCE")]
    out = tmp_path / "report.html"
    render_report(QUERY, results, out, attribution=credits)
    return out.read_text(encoding="utf-8")


def test_report_shows_author_licence_and_link(tmp_path):
    credits = {"fixtures/obama_1.jpg": {"author": "Jane Doe", "license": "CC BY-SA 4.0", "source": SOURCE}}
    page = _report(tmp_path, credits)
    assert "Jane Doe" in page and "CC BY-SA 4.0" in page and f'href="{SOURCE}"' in page


def test_report_without_attribution_has_no_credit_line(tmp_path):
    assert "Photo:" not in _report(tmp_path, {})
    assert "Photo:" not in _report(tmp_path, None)


def test_report_escapes_markup_in_credits(tmp_path):
    credits = {"fixtures/obama_1.jpg": {
        "author": "<img src=x onerror=alert(1)>", "license": "<b>CC</b>", "source": "https://evil.example/",
    }}
    page = _report(tmp_path, credits)
    assert "<img src=x" not in page and "<b>CC</b>" not in page
    assert "&lt;img src=x" in page
    assert "evil.example" not in page  # not a Commons page, so no link


def test_cli_report_credits_the_photos(tmp_path):
    dataset = tmp_path / "pool"
    shutil.copytree(FIXTURES / "dataset", dataset)
    _write(dataset, {"Barack_Obama/Barack_Obama_0001.jpg": {"author": "Pool Author", "license": "CC0", "source": SOURCE}})
    out = tmp_path / "report.html"

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "match.py"), "--image", str(QUERY), "--dataset", str(dataset),
         "--threshold-low", "0", "--threshold-high", "1", "--report-out", str(out)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Pool Author" in out.read_text(encoding="utf-8")
