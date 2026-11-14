"""Processor — the main loop.

Reads commands.txt line-by-line, dispatches each command to its handler.
Accumulates output rows in buffers, then flushes to CSV at the end.
"""
from __future__ import annotations
import logging
from pathlib import Path

from src.engine.commands import (
    AssessCommand, BankEnrolCommand, CalamityCommand, DisburseCommand,
    EnrolCommand, EvalSowingCommand, EvalWeatherCommand, FinaliseYieldCommand,
    OptOutCommand, PrintClaimsCommand, PrintDisbursementCommand, PrintPremiumCommand,
)
from src.engine.handlers import (
    handle_assess, handle_bank_enrol, handle_calamity, handle_disburse,
    handle_enrol, handle_eval_sowing, handle_eval_weather, handle_finalise_yield,
    handle_opt_out, handle_print_claims, handle_print_disbursement, handle_print_premium,
)
from src.engine.state import EngineState
from src.io.command_parser import parse_commands
from src.io.writers import write_claims, write_disbursement, write_premium_statement

log = logging.getLogger("processor")


class Processor:
    def __init__(self, state: EngineState, out_dir: Path):
        self.state = state
        self.out_dir = out_dir
        self.buffer: dict[str, list] = {
            "premium": [], "claims": [], "disbursement": []
        }

    def run(self, commands_path: Path) -> None:
        for cmd in parse_commands(commands_path):
            try:
                self._dispatch(cmd)
            except Exception as e:  # noqa: BLE001
                log.error("command failed: %r (%s)", cmd, e, exc_info=True)

    def _dispatch(self, cmd) -> None:
        s = self.state
        if isinstance(cmd, BankEnrolCommand):
            handle_bank_enrol(cmd, s)
        elif isinstance(cmd, EnrolCommand):
            handle_enrol(cmd, s)
        elif isinstance(cmd, OptOutCommand):
            handle_opt_out(cmd, s)
        elif isinstance(cmd, EvalWeatherCommand):
            handle_eval_weather(cmd, s)
        elif isinstance(cmd, EvalSowingCommand):
            handle_eval_sowing(cmd, s)
        elif isinstance(cmd, CalamityCommand):
            handle_calamity(cmd, s)
        elif isinstance(cmd, AssessCommand):
            handle_assess(cmd, s)
        elif isinstance(cmd, FinaliseYieldCommand):
            handle_finalise_yield(cmd, s)
        elif isinstance(cmd, DisburseCommand):
            handle_disburse(cmd, s)
        elif isinstance(cmd, PrintPremiumCommand):
            handle_print_premium(cmd, s, self.buffer)
        elif isinstance(cmd, PrintClaimsCommand):
            handle_print_claims(cmd, s, self.buffer)
        elif isinstance(cmd, PrintDisbursementCommand):
            handle_print_disbursement(cmd, s, self.buffer)
        else:
            log.warning("unknown command type: %r", cmd)

    def flush(self) -> None:
        write_premium_statement(self.out_dir / "premium_statement.csv", self.buffer["premium"])
        write_claims(self.out_dir / "claims.csv", self.buffer["claims"])
        write_disbursement(self.out_dir / "disbursement.csv", self.buffer["disbursement"])
        log.info(
            "wrote: premium=%d claims=%d disbursement=%d",
            len(self.buffer["premium"]), len(self.buffer["claims"]),
            len(self.buffer["disbursement"]),
        )
