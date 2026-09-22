import json
import shutil
import subprocess
import sys
from pathlib import Path

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


def _parse_output_line(line: str):
    person, rest = line.split(":", 1)
    score_str, label = rest.strip().split()
    return person, float(score_str), label


def test_help_documents_threshold_flags():
    result = run_match("--help")
    assert result.returncode == 0
    assert "--threshold-low" in result.stdout
    assert "--threshold-high" in result.stdout


def test_errors_without_config_or_threshold_flags(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    # No data/config.json sibling, no CLI threshold flags.
    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
    )
    assert result.returncode == 1
    assert result.stderr.strip() != ""


def test_thresholds_loaded_from_config_file(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"threshold_low": 0.0, "threshold_high": 1.0}))

    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
        "--config", str(config_path),
    )
    assert result.returncode == 0
    # threshold_high=1.0 means nothing can exceed it -> everything LOW_CONFIDENCE or NO_MATCH.
    lines = [line for line in result.stdout.strip().splitlines() if line]
    labels = {label for _, _, label in (_parse_output_line(l) for l in lines)}
    assert "HIGH_CONFIDENCE" not in labels


def test_cli_override_takes_precedence_over_config_file(tmp_path):
    dataset_dir = _make_dataset(tmp_path)
    config_path = tmp_path / "config.json"
    # Config says everything is HIGH_CONFIDENCE (thresholds near -1).
    config_path.write_text(json.dumps({"threshold_low": -1.0, "threshold_high": -1.0}))

    # CLI override raises threshold_high so nothing qualifies as HIGH_CONFIDENCE.
    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
        "--config", str(config_path),
        "--threshold-high", "1.0",
    )
    assert result.returncode == 0
    lines = [line for line in result.stdout.strip().splitlines() if line]
    labels = {label for _, _, label in (_parse_output_line(l) for l in lines)}
    assert "HIGH_CONFIDENCE" not in labels


def test_classification_labels_reflect_thresholds(tmp_path):
    dataset_dir = _make_dataset(tmp_path)

    result = run_match(
        "--image", str(FIXTURES / "obama_query.jpg"),
        "--dataset", str(dataset_dir),
        "--threshold-low", "0.65",
        "--threshold-high", "0.73",
    )
    assert result.returncode == 0
    lines = [line for line in result.stdout.strip().splitlines() if line]
    by_person_score = {}
    for person, score, label in (_parse_output_line(l) for l in lines):
        by_person_score.setdefault(person, []).append((score, label))

    for scores_labels in by_person_score.values():
        for score, label in scores_labels:
            if score >= 0.73:
                assert label == "HIGH_CONFIDENCE"
            elif score >= 0.65:
                assert label == "LOW_CONFIDENCE"
            else:
                assert label == "NO_MATCH"
