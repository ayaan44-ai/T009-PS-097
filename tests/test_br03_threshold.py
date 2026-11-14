"""BR-03 threshold yield — best 5 of 7 × indemnity."""
from decimal import Decimal
import pytest

from src.domain.models import NotifiedUnit, YieldHistory
from src.config.enums import CropCategory, RiskLevel
from src.rules.br03_threshold import threshold_yield


def _unit(unit_id: str, indemnity: int) -> NotifiedUnit:
    return NotifiedUnit(
        unit_id=unit_id, district="D", block="B", crop="C",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.LOW, indemnity_level_pct=indemnity,
        sum_insured_per_ha=Decimal("52000"), actuarial_rate_pct=Decimal("9"),
        normal_area_ha=Decimal("4200"), station_id="ST-01",
        normal_rain_jun_jul_mm=Decimal("520"), block_yield_kg_ha=3650,
    )


def test_nu01_threshold_90pct() -> None:
    unit = _unit("NU-01", 90)
    hist = [YieldHistory("NU-01", y, v) for y, v in [
        (2019, 3509), (2020, 3980), (2021, 3992), (2022, 4420),
        (2023, 3488), (2024, 3637), (2025, 4101),
    ]]
    assert threshold_yield(unit, hist) == Decimal("3623.40")


def test_nu02_threshold_80pct() -> None:
    unit = _unit("NU-02", 80)
    hist = [YieldHistory("NU-02", y, v) for y, v in [
        (2019, 4244), (2020, 4537), (2021, 4233), (2022, 4468),
        (2023, 4517), (2024, 4495), (2025, 4283),
    ]]
    assert threshold_yield(unit, hist) == Decimal("3568.00")


def test_nu04_threshold_70pct() -> None:
    unit = _unit("NU-04", 70)
    hist = [YieldHistory("NU-04", y, v) for y, v in [
        (2019, 2150), (2020, 1854), (2021, 1880), (2022, 2339),
        (2023, 2307), (2024, 2229), (2025, 2352),
    ]]
    assert threshold_yield(unit, hist) == Decimal("1592.78")


def test_wrong_year_count_raises() -> None:
    unit = _unit("X", 90)
    hist = [YieldHistory("X", 2020, 1000)] * 6   # 6, not 7
    with pytest.raises(ValueError):
        threshold_yield(unit, hist)


def test_identical_yields() -> None:
    unit = _unit("X", 90)
    hist = [YieldHistory("X", y, 5000) for y in range(2019, 2026)]
    # avg = 5000, × 0.90 = 4500.00
    assert threshold_yield(unit, hist) == Decimal("4500.00")
