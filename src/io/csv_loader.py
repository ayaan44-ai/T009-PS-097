"""Generic CSV reader + master data validation."""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Iterator


class MasterDataError(Exception):
    """Raised when an input CSV is missing, malformed, or inconsistent."""


def read_csv(path: Path) -> Iterator[dict[str, str]]:
    if not path.exists():
        raise MasterDataError(f"missing input file: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise MasterDataError(f"empty CSV (no header): {path}")
        for row in reader:
            yield {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}
