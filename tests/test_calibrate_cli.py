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
        "--config-out", str(config_out),
    )
    assert result.returncode == 0, result.stderr


def test_calibrate_writes_config_with_both_thresholds(tmp_path):
    config_out = tmp_path / "config.json"
    run_calibrate(
        "--calibration-dir", str(FIXTURES / "calibration"),
        "--config-out", str(config_out),
    )

    assert config_out.exists()
    payload = json.loads(config_out.read_text())
    assert isinstance(payload["threshold_low"], (int, float))
    assert isinstance(payload["threshold_high"], (int, float))
    assert payload["threshold_high"] >= payload["threshold_low"]
