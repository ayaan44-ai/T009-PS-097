"""BR-04 — Area-yield claim from crop-cutting experiments.

Rules:
- actual yield = mean(CCE yields) if >=4 CCEs for the unit
- else actual yield = block_yield_kg_ha, and a 10% haircut applies to gross claim
- if actual >= threshold: no claim (return None)
- else: claim/ha = (threshold − actual) / threshold × SI/ha
- gross claim = claim/ha × area_insured × (0.9 if used block yield else 1.0)
- zero-payout claims emit no row (locked decision L12)
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal

from src.config.constants import BLOCK_YIELD_HAIRCUT, MIN_CCES
from src.config.enums import ClaimStatus, ClaimType
from src.domain.models import CCEYield, Claim, Enrolment, NotifiedUnit
from src.util.money import round_rupee


def actual_yield(
    unit: NotifiedUnit, cces: list[CCEYield]
) -> tuple[Decimal, bool]:
    """Return (actual_yield_kg_ha, used_block_yield)."""
    if len(cces) >= MIN_CCES:
        avg = Decimal(sum(c.yield_kg_ha for c in cces)) / Decimal(len(cces))
        return avg, False
    return Decimal(unit.block_yield_kg_ha), True


def area_yield_claim(
    enrolment: Enrolment,
    unit: NotifiedUnit,
    threshold: Decimal,
    cces: list[CCEYield],
    finalise_date: date,
) -> Claim | None:
    """Return the AREA_YIELD claim, or None if no shortfall."""
    actual, used_block = actual_yield(unit, cces)
    if actual >= threshold:
        return None
    shortfall_per_ha = (threshold - actual) / threshold * unit.sum_insured_per_ha
    gross = shortfall_per_ha * enrolment.area_insured_ha
    if used_block:
        gross = gross * BLOCK_YIELD_HAIRCUT
    gross = round_rupee(gross)
    if gross <= Decimal("0"):
        return None
    return Claim(
        unit_id=enrolment.unit_id,
        farmer_id=enrolment.farmer_id,
        claim_type=ClaimType.AREA_YIELD,
        trigger_band="N/A",
        gross_amount=gross,
        status=ClaimStatus.PENDING,
        rule_id="BR-04",
        finalisation_date=finalise_date,
        created_date=finalise_date,
    )
