import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def run_match(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "match.py"), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _make_dataset(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset_dir)
    return dataset_dir


def test_report_written_after_successful_match(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    report_path = tmp_path / "report.html"

    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
        "--threshold-low", "0.0",
        "--threshold-high", "1.0",
        "--report-out", str(report_path),
    )

    assert result.returncode == 0
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Barack_Obama" in content
    assert "data:image/jpeg;base64," in content


def test_no_report_written_on_no_face_error(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    report_path = tmp_path / "report.html"

    blank_path = tmp_path / "blank.jpg"
    blank = np.full((300, 300, 3), 255, dtype=np.uint8)
    cv2.imwrite(str(blank_path), blank)

    result = run_match(
        "--image", str(blank_path),
        "--dataset", str(dataset_dir),
        "--threshold-low", "0.0",
        "--threshold-high", "1.0",
        "--report-out", str(report_path),
    )

    assert result.returncode == 1
    assert not report_path.exists()


def test_report_parent_directory_created_if_missing(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    report_path = tmp_path / "nested" / "does" / "not" / "exist" / "report.html"

    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
        "--threshold-low", "0.0",
        "--threshold-high", "1.0",
        "--report-out", str(report_path),
    )

    assert result.returncode == 0
    assert report_path.exists()
