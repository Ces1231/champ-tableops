from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_showcase_flag_is_exposed():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(repo_root / "demo" / "tableops_cli.py"), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "--showcase" in result.stdout
    assert "Intel OpenVINO" in result.stdout
