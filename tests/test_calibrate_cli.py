import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def run_calibrate(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "calibrate.py"), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_calibrate_exits_zero_on_fixture_calibration_dataset(tmp_path):
    config_out = tmp_path / "config.json"
    result = run_calibrate(
        "--calibration-dir", str(FIXTURES / "calibration"),
        "--dataset", str(FIXTURES / "dataset"),
        "--config-out", str(config_out),
    )
    assert result.returncode == 0, result.stderr


def test_calibrate_writes_config_with_both_thresholds(tmp_path):
    config_out = tmp_path / "config.json"
    run_calibrate(
        "--calibration-dir", str(FIXTURES / "calibration"),
        "--dataset", str(FIXTURES / "dataset"),
        "--config-out", str(config_out),
    )

    assert config_out.exists()
    payload = json.loads(config_out.read_text())
    assert isinstance(payload["threshold_low"], (int, float))
    assert isinstance(payload["threshold_high"], (int, float))
    assert payload["threshold_high"] >= payload["threshold_low"]


def test_calibrate_errors_without_two_calibration_identities(tmp_path):
    # One identity gives no different-person pairs, so no EER point exists.
    calibration_dir = tmp_path / "calibration"
    (calibration_dir / "only_one").mkdir(parents=True)
    for src in (FIXTURES / "calibration" / "Kit_Harington").iterdir():
        (calibration_dir / "only_one" / src.name).write_bytes(src.read_bytes())
    config_out = tmp_path / "config.json"

    result = run_calibrate(
        "--calibration-dir", str(calibration_dir),
        "--dataset", str(FIXTURES / "dataset"),
        "--config-out", str(config_out),
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "Error: need faces of at least 2 people" in result.stderr
    assert not config_out.exists()
