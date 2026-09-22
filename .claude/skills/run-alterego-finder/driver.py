#!/usr/bin/env python
"""Driver for AlterEgo Finder: runs the real CLI pipeline end to end against
the repo's own test fixtures (no dataset of your own required).

Usage (from the repo root, in any shell):
    python .claude/skills/run-alterego-finder/driver.py

Exits 0 and prints "All driver checks passed." on success; raises an
AssertionError with the failing step's output otherwise.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

# .claude/skills/run-alterego-finder/driver.py -> repo root is 3 levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        config_path = tmp_dir / "config.json"

        print("== calibrate.py: derive thresholds from the fixture calibration set ==")
        result = run([
            sys.executable, "calibrate.py",
            "--calibration-dir", "tests/fixtures/calibration",
            "--config-out", str(config_path),
        ])
        assert result.returncode == 0, "calibrate.py failed"
        assert config_path.exists(), "calibrate.py did not write config.json"

        print("\n== match.py: happy path (Obama query vs Obama/Biden fixture dataset) ==")
        result = run([
            sys.executable, "match.py",
            "--image", "tests/fixtures/obama_query.jpg",
            "--dataset", "tests/fixtures/dataset",
            "--config", str(config_path),
        ])
        assert result.returncode == 0, "match.py happy path failed"
        assert "Barack_Obama" in result.stdout and "HIGH_CONFIDENCE" in result.stdout, (
            "expected a HIGH_CONFIDENCE Barack_Obama line in match.py's output"
        )

        print("\n== match.py: no-face error path ==")
        blank_path = tmp_dir / "blank.jpg"
        blank = np.full((300, 300, 3), 255, dtype=np.uint8)
        ok = cv2.imwrite(str(blank_path), blank)
        assert ok, f"failed to write blank fixture image to {blank_path}"

        result = run([
            sys.executable, "match.py",
            "--image", str(blank_path),
            "--dataset", "tests/fixtures/dataset",
            "--config", str(config_path),
        ])
        assert result.returncode == 1, "expected exit code 1 for a faceless query image"
        assert "Error: No face detected in input image" in result.stderr

    print("\nAll driver checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
