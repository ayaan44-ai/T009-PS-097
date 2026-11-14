"""BR-05 deficit rainfall — strict < boundaries."""
from decimal import Decimal
from src.rules.br05_deficit import deficit_band


def test_ec01_exactly_75pct_no_payout() -> None:
    """EC-01: exactly 75.0% of normal -> no payout."""
    pct, band = deficit_band(Decimal("390.0"), Decimal("520.0"))   # 75.0% exactly
    assert pct == Decimal("0")
    assert band == "0%"


def test_nu02_69_64pct_returns_20pct_band() -> None:
    pct, band = deficit_band(Decimal("390.0"), Decimal("560.0"))
    assert pct == Decimal("20")
    assert band == "20%"


def test_below_40_pct_returns_60pct_band() -> None:
    pct, band = deficit_band(Decimal("199.5"), Decimal("500.0"))   # 39.9%
    assert pct == Decimal("60")
    assert band == "60%"


def test_exactly_40_pct_returns_40pct_band() -> None:
    """40.0% is NOT below 40% -> 40% band, not 60%."""
    pct, band = deficit_band(Decimal("200.0"), Decimal("500.0"))
    assert pct == Decimal("40")
    assert band == "40%"


def test_exactly_60_pct_returns_20pct_band() -> None:
    """60.0% is NOT below 60% -> 20% band, not 40%."""
    pct, band = deficit_band(Decimal("300.0"), Decimal("500.0"))
    assert pct == Decimal("20")
    assert band == "20%"


def test_zero_rain_returns_60pct() -> None:
    pct, band = deficit_band(Decimal("0"), Decimal("500.0"))
    assert pct == Decimal("60")
