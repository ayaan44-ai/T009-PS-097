"""Parse commands.txt line-by-line into Command objects.

Invalid lines are logged and skipped — never crash on one bad line.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Iterator

from src.engine.commands import (
    AssessCommand, BankEnrolCommand, CalamityCommand, DisburseCommand,
    EnrolCommand, EvalSowingCommand, EvalWeatherCommand, FinaliseYieldCommand,
    OptOutCommand, PrintClaimsCommand, PrintDisbursementCommand, PrintPremiumCommand,
)
from src.util.dates import parse_date, parse_timestamp
from src.util.money import D

log = logging.getLogger("command_parser")


def parse_commands(path: Path) -> Iterator:
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            verb = parts[0]
            try:
                yield _build(verb, parts)
            except Exception as e:  # noqa: BLE001
                log.warning("skip bad command line %d: %s (%s)", line_no, line, e)


def _build(verb: str, parts: list[str]):
    if verb == "ENROL":
        return EnrolCommand(
            enrolment_id=parts[1], farmer_id=parts[2], unit_id=parts[3],
            survey_no=parts[4], area_sown_ha=D(parts[5]), file_date=parse_date(parts[6]),
        )
    if verb == "BANK_ENROL":
        return BankEnrolCommand(
            enrolment_id=parts[1], farmer_id=parts[2], unit_id=parts[3],
            survey_no=parts[4], area_sown_ha=D(parts[5]), file_date=parse_date(parts[6]),
        )
    if verb == "OPT_OUT":
        return OptOutCommand(
            farmer_id=parts[1], unit_id=parts[2], request_date=parse_date(parts[3]),
        )
    if verb == "EVALUATE_WEATHER":
        return EvalWeatherCommand(
            unit_id=parts[1], trigger=parts[2], eval_date=parse_date(parts[3]),
        )
    if verb == "EVALUATE_SOWING":
        return EvalSowingCommand(unit_id=parts[1], eval_date=parse_date(parts[2]))
    if verb == "CALAMITY_NOTIFY":
        return CalamityCommand(
            notification_id=parts[1], farmer_id=parts[2], unit_id=parts[3],
            event_type=parts[4], event_ts=parse_timestamp(parts[5]),
            notify_ts=parse_timestamp(parts[6]), area_affected_ha=D(parts[7]),
        )
    if verb == "ASSESS":
        return AssessCommand(
            notification_id=parts[1], loss_pct=D(parts[2]), assess_date=parse_date(parts[3]),
        )
    if verb == "FINALISE_YIELD":
        return FinaliseYieldCommand(unit_id=parts[1], finalise_date=parse_date(parts[2]))
    if verb == "DISBURSE":
        return DisburseCommand(unit_id=parts[1], payment_date=parse_date(parts[2]))
    if verb == "PRINT_PREMIUM_STATEMENT":
        return PrintPremiumCommand(unit_id=parts[1])
    if verb == "PRINT_CLAIMS":
        return PrintClaimsCommand(unit_id=parts[1])
    if verb == "PRINT_DISBURSEMENT_FILE":
        return PrintDisbursementCommand(as_of_date=parse_date(parts[1]))
    raise ValueError(f"unknown verb: {verb}")
