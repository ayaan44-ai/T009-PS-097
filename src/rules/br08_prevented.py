"""BR-08 — Prevented sowing assessment.

Rule:
- On 15 Aug (cut-off + 15 days), if sown area < 25% of normal area,
  every active enrolment gets 25% of its sum insured.
- Unit is then TERMINATED: no future claims (weather, area-yield).
- Prior weather payments are NOT clawed back (EC-05).

Strict `<`: exactly 25% does NOT trigger.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal

from src.config.constants import PREVENTED_PAYOUT_PCT, PREVENTED_SOWN_FRACTION
from src.config.enums import ClaimStatus, ClaimType
from src.domain.models import Claim, Enrolment, NotifiedUnit, SowingReport
from src.util.money import D, round_rupee


def is_prevented(sowing_15aug: SowingReport, unit: NotifiedUnit) -> bool:
    """Return True if sown < 25% of normal area."""
    threshold = unit.normal_area_ha * PREVENTED_SOWN_FRACTION
    return sowing_15aug.area_sown_ha < threshold


def prevented_claim(
    enrolment: Enrolment,
    unit: NotifiedUnit,
    eval_date: date,
) -> Claim:
    """Build the PREVENTED_SOWING claim for one enrolment."""
    amount = round_rupee(enrolment.sum_insured * PREVENTED_PAYOUT_PCT / Decimal("100"))
    return Claim(
        unit_id=enrolment.unit_id,
        farmer_id=enrolment.farmer_id,
        claim_type=ClaimType.PREVENTED_SOWING,
        trigger_band="25%",
        gross_amount=amount,
        status=ClaimStatus.PENDING,
        rule_id="BR-08",
        finalisation_date=eval_date,
        created_date=eval_date,
    )
