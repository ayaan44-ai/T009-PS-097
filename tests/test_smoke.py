"""Smoke tests: prove the pipeline runs end-to-end on real sample data."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def test_src_importable() -> None:
    import src
    assert src is not None


def test_full_pipeline_runs(tmp_path: Path) -> None:
    """Run run.py on the real data/ folder; assert 3 output CSVs produced."""
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    out_dir = tmp_path / "out"

    result = subprocess.run(
        [sys.executable, "run.py", str(data_dir), str(out_dir)],
        cwd=root, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr

    # Three output files must exist and be non-empty
    for name in ("premium_statement.csv", "claims.csv", "disbursement.csv"):
        f = out_dir / name
        assert f.exists(), f"{name} not produced"
        assert f.stat().st_size > 0, f"{name} is empty"

    # premium_statement should have ~148 lines (147 data + 1 header)
    premium = (out_dir / "premium_statement.csv").read_text().splitlines()
    assert len(premium) > 100, f"premium too small: {len(premium)} lines"

    # claims should have all claim types present
    claims_text = (out_dir / "claims.csv").read_text()
    for ct in ("AREA_YIELD", "DEFICIT_RAIN", "DRY_SPELL", "EXCESS_RAIN",
               "LOCALISED", "PREVENTED_SOWING"):
        assert ct in claims_text, f"missing claim type: {ct}"
