"""Smoke tests: prove the skeleton works."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def test_src_importable() -> None:
    import src
    assert src is not None


def test_run_py_runs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "run.py", str(tmp_path / "data"), str(tmp_path / "out")],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "PS-097 skeleton OK" in result.stdout
