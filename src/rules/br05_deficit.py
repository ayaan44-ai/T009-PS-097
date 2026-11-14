"""BR-05 — Deficit rainfall trigger (1 Jun – 31 Jul).

Rules (strict `<` everywhere):
- cumulative rain / normal rain × 100 < 40%  → 60% SI
- < 60% → 40% SI
- < 75% → 20% SI
- else → no payout (0%)
- Missing day in the window contributes 0 mm (locked decision L7)
- Exactly 75% is NOT below 75% → no payout (EC-01)
"""
from __future__ import annotations
from decimal import Decimal

from src.config.constants import DEFICIT_BANDS


def deficit_band(rain_sum_mm: Decimal, normal_mm: Decimal) -> tuple[Decimal, str]:
    """Return (payout_pct_of_SI, trigger_band_string).

    payout_pct is 0 if no band matched (rain >= 75% of normal).
    Bands are checked highest-payout-first to implement 'highest band only'.
    """
    if normal_mm <= Decimal("0"):
        return Decimal("0"), "0%"
    pct_of_normal = rain_sum_mm / normal_mm * Decimal("100")
    for upper_bound, payout, band_str in DEFICIT_BANDS:
        # DEFICIT_BANDS ordered as (40,60%), (60,40%), (75,20%)
        if pct_of_normal < upper_bound:
            return payout, band_str
    return Decimal("0"), "0%"
