"""PS-097 command-line entry point.

Usage:
    python run.py <data_dir> <out_dir>
"""
from __future__ import annotations
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("Usage: python run.py <data_dir> <out_dir>", file=sys.stderr)
        return 2
    data_dir = Path(argv[0])
    out_dir = Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"PS-097 skeleton OK: data={data_dir} out={out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
