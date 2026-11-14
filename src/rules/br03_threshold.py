"""BR-03 — Threshold yield.

Formula:
    seven_years = yield_kg_ha for 2019..2025 (7 values)
    best_five   = sorted(seven_years)[2:]   (drop the two lowest)
    avg_best5   = sum(best_five) / 5
    threshold   = avg_best5 × indemnity_level_pct / 100
"""
from __future__ import annotations
from decimal import Decimal

from src.config.constants import BEST_N_YEARS, YIELD_HISTORY_YEARS
from src.domain.models import NotifiedUnit, YieldHistory


def threshold_yield(unit: NotifiedUnit, history: list[YieldHistory]) -> Decimal:
    """Compute threshold yield for a unit from its 7-year yield history."""
    if len(history) != YIELD_HISTORY_YEARS:
        raise ValueError(
            f"unit {unit.unit_id} has {len(history)} years, expected {YIELD_HISTORY_YEARS}"
        )
    yields_sorted = sorted(h.yield_kg_ha for h in history)
    best_five = yields_sorted[YIELD_HISTORY_YEARS - BEST_N_YEARS:]
    avg_best5 = Decimal(sum(best_five)) / Decimal(BEST_N_YEARS)
    threshold = avg_best5 * Decimal(unit.indemnity_level_pct) / Decimal("100")
    return threshold.quantize(Decimal("0.01"))
