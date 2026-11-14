"""BR-06 dry spell — EC-02, EC-03, missing-day break, cap."""
from datetime import date
from decimal import Decimal
from src.rules.br06_dry_spell import dry_spell


def d(y, m, dd):
    return date(y, m, dd)


def test_ec02_exactly_20_days_ending_30sep() -> None:
    """EC-02: 20 consecutive dry days ending 30 Sep qualifies."""
    rain = {d(2026, 9, 10): Decimal("13.5")}     # 10 Sep wet (breaks prior)
    for i in range(11, 31):
        rain[d(2026, 9, i)] = Decimal("0.5")
    result = dry_spell(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert result.pct == Decimal("15")
    assert len(result.spells) == 1


def test_ec03_two_spells_separated_by_exactly_2_5mm() -> None:
    """EC-03: 2.5 mm day is NOT dry -> breaks spell -> two spells -> 25%."""
    rain = {}
    for i in range(4, 26):
        rain[d(2026, 7, i)] = Decimal("0.0")
    rain[d(2026, 7, 26)] = Decimal("2.5")        # exactly 2.5, NOT dry
    for i in range(27, 32):
        rain[d(2026, 7, i)] = Decimal("0.0")
    for i in range(1, 18):
        rain[d(2026, 8, i)] = Decimal("0.0")
    result = dry_spell(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert result.pct == Decimal("25")
    assert len(result.spells) == 2


def test_missing_day_breaks_spell() -> None:
    """A missing day (no row) is NOT dry and breaks the spell."""
    rain = {}
    for i in range(1, 21):
        if i != 10:                               # 10 Aug missing
            rain[d(2026, 8, i)] = Decimal("0.0")
    result = dry_spell(rain, d(2026, 7, 1), d(2026, 9, 30))
    # 9-day + 10-day split -> neither qualifies
    assert result.pct == Decimal("0")
    assert len(result.spells) == 0


def test_19_days_does_not_qualify() -> None:
    rain = {d(2026, 8, i): Decimal("0.0") for i in range(1, 20)}   # 19 days
    result = dry_spell(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert result.pct == Decimal("0")


def test_third_spell_capped_at_25() -> None:
    """Three qualifying spells -> still 25% (cap)."""
    rain = {}
    # 20 days: 1-20 Aug
    for i in range(1, 21):
        rain[d(2026, 8, i)] = Decimal("0.0")
    # 20 days: 1-20 Sep
    for i in range(1, 21):
        rain[d(2026, 9, i)] = Decimal("0.0")
    result = dry_spell(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert result.pct == Decimal("25")


def test_no_dry_days_no_payout() -> None:
    rain = {d(2026, 8, i): Decimal("10.0") for i in range(1, 32)}
    result = dry_spell(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert result.pct == Decimal("0")
