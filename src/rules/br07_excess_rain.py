"""BR-07 — Excess rainfall + station replacement.

Excess rain:
- Any 3-consecutive-day total > 200 mm (strict) between 1 Jul and 30 Sep
  → 15% SI (once per season).
- A missing day inside a 3-day window skips that window.

Station replacement (used by all weather triggers):
- Count missing days in the whole series 1 Jun – 30 Sep.
- If missing_count > 10 → find nearest station within 25 km.
- If found → use replacement's data.
- If not → return None (NOT_ASSESSABLE).
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal

from src.config.constants import (
    EXCESS_PAYOUT_PCT,
    EXCESS_THRESHOLD_MM,
    EXCESS_WINDOW_DAYS,
    MISSING_DAY_LIMIT,
    REPLACEMENT_MAX_KM,
)


def excess_rain_qualifies(
    rain_by_date: dict[date, Decimal],
    start: date,
    end: date,
) -> tuple[bool, str]:
    """Return (qualifies, band_str)."""
    days: list[date] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur = date.fromordinal(cur.toordinal() + 1)

    for i in range(len(days) - EXCESS_WINDOW_DAYS + 1):
        window = days[i:i + EXCESS_WINDOW_DAYS]
        if any(d not in rain_by_date for d in window):
            continue
        total = sum((rain_by_date[d] for d in window), Decimal("0"))
        if total > EXCESS_THRESHOLD_MM:
            return True, "15%"
    return False, "0%"


def effective_station(
    primary_station: str,
    missing_count: int,
    distances: dict[tuple[str, str], Decimal],
) -> str | None:
    """Return the station to use for weather triggers, or None if NOT_ASSESSABLE."""
    if missing_count <= MISSING_DAY_LIMIT:
        return primary_station
    best: tuple[str, Decimal] | None = None
    for (a, b), km in distances.items():
        if a == primary_station:
            candidate = b
        elif b == primary_station:
            candidate = a
        else:
            continue
        if best is None or km < best[1]:
            best = (candidate, km)
    if best is None or best[1] > REPLACEMENT_MAX_KM:
        return None
    return best[0]
