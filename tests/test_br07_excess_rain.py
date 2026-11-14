"""BR-07 excess rain + station replacement."""
from datetime import date
from decimal import Decimal
from src.rules.br07_excess_rain import excess_rain_qualifies, effective_station


def d(y, m, dd):
    return date(y, m, dd)


def test_st03_214_6mm_qualifies() -> None:
    rain = {
        d(2026, 8, 12): Decimal("88.4"),
        d(2026, 8, 13): Decimal("79.6"),
        d(2026, 8, 14): Decimal("46.6"),
    }
    ok, band = excess_rain_qualifies(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert ok is True
    assert band == "15%"


def test_exactly_200mm_does_not_qualify() -> None:
    """Strict `>`: 200.0 exactly does NOT qualify."""
    rain = {
        d(2026, 8, 1): Decimal("100.0"),
        d(2026, 8, 2): Decimal("100.0"),
        d(2026, 8, 3): Decimal("0.0"),
    }
    ok, band = excess_rain_qualifies(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert ok is False


def test_200_1mm_qualifies() -> None:
    rain = {
        d(2026, 8, 1): Decimal("100.0"),
        d(2026, 8, 2): Decimal("100.1"),
        d(2026, 8, 3): Decimal("0.0"),
    }
    ok, _ = excess_rain_qualifies(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert ok is True


def test_missing_day_skips_window() -> None:
    """3-day window with a missing day doesn't qualify (can't sum)."""
    rain = {
        d(2026, 8, 1): Decimal("100.0"),
        # 2 Aug missing
        d(2026, 8, 3): Decimal("150.0"),
    }
    ok, _ = excess_rain_qualifies(rain, d(2026, 7, 1), d(2026, 9, 30))
    assert ok is False


def test_ec07_exactly_10_missing_stays() -> None:
    """EC-07: exactly 10 missing days -> no replacement."""
    distances = {("ST-02", "ST-03"): Decimal("24.6")}
    assert effective_station("ST-02", 10, distances) == "ST-02"


def test_st02_12_missing_replaced_by_st03() -> None:
    distances = {("ST-02", "ST-03"): Decimal("24.6")}
    assert effective_station("ST-02", 12, distances) == "ST-03"


def test_no_station_within_25km_returns_none() -> None:
    distances = {("ST-01", "ST-03"): Decimal("57.3")}
    assert effective_station("ST-03", 15, distances) is None
