"""BR-01 — Premium calculation and subsidy split.

Formula:
    sum_insured     = SI/ha × area_insured
    total_premium   = sum_insured × actuarial_rate%
    farmer_premium  = sum_insured × farmer_share%   (2% Kharif food, 5% commercial)
    subsidy_pool    = total_premium − farmer_premium
    state_subsidy   = floor(pool/2)
    centre_subsidy  = pool − state_subsidy    (absorbs odd rupee)

All amounts rounded to rupee (half-up).
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

from src.config.constants import FARMER_SHARE_PCT
from src.domain.models import NotifiedUnit
from src.util.money import D, round_rupee


@dataclass(frozen=True)
class PremiumBreakdown:
    sum_insured: Decimal
    total_premium: Decimal
    farmer_premium: Decimal
    state_subsidy: Decimal
    centre_subsidy: Decimal


def farmer_share_pct(unit: NotifiedUnit) -> Decimal:
    """Look up farmer's out-of-pocket percentage for this unit."""
    key = (unit.season, unit.crop_category.value)
    if key not in FARMER_SHARE_PCT:
        raise ValueError(f"no farmer share for {key}")
    return FARMER_SHARE_PCT[key]


def compute_premium(unit: NotifiedUnit, area_ha: Decimal) -> PremiumBreakdown:
    """Compute the full premium breakdown for one enrolment."""
    area = D(area_ha)
    si = round_rupee(unit.sum_insured_per_ha * area)
    total = round_rupee(si * unit.actuarial_rate_pct / Decimal("100"))
    farmer = round_rupee(si * farmer_share_pct(unit) / Decimal("100"))
    pool = total - farmer
    state = (pool / Decimal("2")).quantize(Decimal("1"))
    centre = pool - state
    return PremiumBreakdown(
        sum_insured=si,
        total_premium=total,
        farmer_premium=farmer,
        state_subsidy=state,
        centre_subsidy=centre,
    )
