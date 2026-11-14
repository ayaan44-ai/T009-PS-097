"""BR-06 — Dry-spell trigger (1 Jul – 30 Sep).

Rules:
- A day is "dry" if rainfall < 2.5 mm. Exactly 2.5 mm is NOT dry (EC-03).
- A MISSING day (no row) is NOT dry and BREAKS any in-progress spell.
- Qualifying spells have >= 20 consecutive dry days.
- 1 qualifying spell → 15% SI; 2+ qualifying spells → 25% SI (cap).
- Third+ spells add no further percentage (locked decision L9).
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.config.constants import (
    DRY_DAY_THRESHOLD_MM,
    DRY_SPELL_CAP_PCT,
    DRY_SPELL_FIRST_PCT,
    DRY_SPELL_SECOND_PCT,
    MIN_DRY_SPELL_DAYS,
)


@dataclass(frozen=True)
class DrySpellResult:
    pct: Decimal
    band_str: str
    spells: list[tuple[date, date]]     # (start, end) of each qualifying spell


def dry_spell(
    rain_by_date: dict[date, Decimal],
    start: date,
    end: date,
) -> DrySpellResult:
    """Detect qualifying dry spells between start..end inclusive.

    rain_by_date: only dates that HAVE a row. Missing dates are absent.
    A missing date is NOT dry and BREAKS the current spell.
    """
    spells: list[tuple[date, date]] = []
    current_start: date | None = None
    current_len = 0
    cur = start
    while cur <= end:
        rain = rain_by_date.get(cur)
        is_dry = (rain is not None) and (rain < DRY_DAY_THRESHOLD_MM)
        if is_dry:
            if current_start is None:
                current_start = cur
            current_len += 1
        else:
            # Wet day OR missing day -> close any open spell
            if current_len >= MIN_DRY_SPELL_DAYS and current_start is not None:
                spells.append((current_start, cur.fromordinal(cur.toordinal() - 1)))
            current_start = None
            current_len = 0
        cur = date.fromordinal(cur.toordinal() + 1)
    # Close spell if it runs to end of window
    if current_start is not None and current_len >= MIN_DRY_SPELL_DAYS:
        spells.append((current_start, end))

    if not spells:
        return DrySpellResult(Decimal("0"), "0%", [])
    if len(spells) == 1:
        return DrySpellResult(DRY_SPELL_FIRST_PCT, "15%", spells)
    total = DRY_SPELL_FIRST_PCT + DRY_SPELL_SECOND_PCT
    if total > DRY_SPELL_CAP_PCT:
        total = DRY_SPELL_CAP_PCT
    return DrySpellResult(total, "15%+10%", spells)
