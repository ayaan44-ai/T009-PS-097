"""PS-097 command-line entry point.

Usage:
    python run.py <data_dir> <out_dir> [--log-file PATH] [--log-level LEVEL]
"""
from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run.py",
        description="PS-097 Crop Insurance Claim Engine",
    )
    p.add_argument("data_dir", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--log-file", type=Path, default=None)
    p.add_argument(
        "--log-level", default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = [logging.StreamHandler(sys.stderr)]
    if args.log_file is not None:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
        handlers=handlers,
    )
    log = logging.getLogger("run")
    log.info("data_dir=%s out_dir=%s", args.data_dir, args.out_dir)

    from src.engine.processor import Processor
    from src.engine.state import EngineState
    from src.io.master_loader import load_masters, load_weather

    masters = load_masters(args.data_dir)
    weather = load_weather(args.data_dir)
    state = EngineState(masters=masters, weather=weather)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    processor = Processor(state, args.out_dir)
    processor.run(args.data_dir / "commands.txt")
    processor.flush()
    log.info("run complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
