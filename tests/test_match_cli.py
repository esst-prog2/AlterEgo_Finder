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


def test_help_documents_image_and_dataset_flags():
    result = run_match("--help")
    assert result.returncode == 0
    assert "--image" in result.stdout
    assert "--dataset" in result.stdout


def _parse_output_line(line: str):
    person, rest = line.split(":", 1)
    score_str, label = rest.strip().split()
    return person, float(score_str), label


def test_ranks_correct_identity_above_other(tmp_path):
    dataset_dir = tmp_path / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset_dir)

    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
        "--threshold-low", "0.0",
        "--threshold-high", "1.0",
    )

    assert result.returncode == 0
    lines = [line for line in result.stdout.strip().splitlines() if line]
    parsed = [_parse_output_line(line) for line in lines]
    ranked_people = [person for person, _, _ in parsed]

    assert ranked_people[0] == "Barack_Obama"
    assert "Joe_Biden" in ranked_people
    assert ranked_people.index("Barack_Obama") < ranked_people.index("Joe_Biden")

    # The dataset indexes two Barack_Obama photos, so the name can appear
    # twice; take each person's best (first, since output is sorted
    # descending) score rather than letting a later, weaker line win.
    best_scores: dict[str, float] = {}
    for person, score, _ in parsed:
        best_scores.setdefault(person, score)
    assert best_scores["Barack_Obama"] > best_scores["Joe_Biden"]


def test_exits_1_with_message_when_query_has_no_face(tmp_path):
    dataset_dir = tmp_path / "dataset"
    shutil.copytree(FIXTURES / "dataset", dataset_dir)

    blank_path = tmp_path / "blank.jpg"
    blank = np.full((300, 300, 3), 255, dtype=np.uint8)
    cv2.imwrite(str(blank_path), blank)

    result = run_match(
        "--image", str(blank_path),
        "--dataset", str(dataset_dir),
        "--threshold-low", "0.0",
        "--threshold-high", "1.0",
    )

    assert result.returncode == 1
    assert "Error: No face detected in input image" in result.stderr
