"""BR-02 — Enrolment cut-off, opt-out window, and area cap.

Rules:
- ENROL after 2026-07-31 → REJECTED
- BANK_ENROL after 2026-07-31 → REJECTED (locked decision L4)
- OPT_OUT after 2026-07-24 → REJECTED (stays enrolled)
- area_insured cannot exceed land record area → REJECTED
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.config.constants import ENROLMENT_CUTOFF, OPT_OUT_CUTOFF
from src.domain.models import LandRecord


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str | None = None


def validate_enrolment_date(file_date: date) -> ValidationResult:
    """Enrolment must be on or before the season cut-off (inclusive)."""
    if file_date > ENROLMENT_CUTOFF:
        return ValidationResult(False, "AFTER_CUTOFF")
    return ValidationResult(True)


def validate_opt_out_date(request_date: date) -> ValidationResult:
    """Opt-out must be on or before cut-off minus 7 (inclusive)."""
    if request_date > OPT_OUT_CUTOFF:
        return ValidationResult(False, "OPT_OUT_AFTER_CUTOFF")
    return ValidationResult(True)


def validate_area(area_sown_ha: Decimal, land: LandRecord) -> ValidationResult:
    """Enrolled area cannot exceed land-record area."""
    if area_sown_ha > land.area_ha:
        return ValidationResult(False, "AREA_EXCEEDS_LAND")
    return ValidationResult(True)
