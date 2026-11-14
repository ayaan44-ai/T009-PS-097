"""BR-01 premium tests — matches the manual numbers verified in dev."""
from decimal import Decimal
from src.domain.models import NotifiedUnit
from src.config.enums import CropCategory, RiskLevel
from src.rules.br01_premium import compute_premium


def _nu01() -> NotifiedUnit:
    return NotifiedUnit(
        unit_id="NU-01", district="D", block="B", crop="Paddy",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.LOW, indemnity_level_pct=90,
        sum_insured_per_ha=Decimal("52000"), actuarial_rate_pct=Decimal("9"),
        normal_area_ha=Decimal("4200"), station_id="ST-01",
        normal_rain_jun_jul_mm=Decimal("520"), block_yield_kg_ha=3650,
    )


def test_premium_nu01_2_01ha() -> None:
    pb = compute_premium(_nu01(), Decimal("2.01"))
    assert pb.sum_insured == Decimal("104520")
    assert pb.total_premium == Decimal("9407")
    assert pb.farmer_premium == Decimal("2090")
    assert pb.state_subsidy == Decimal("3658")
    assert pb.centre_subsidy == Decimal("3659")


def test_premium_subsidy_sums_exactly() -> None:
    pb = compute_premium(_nu01(), Decimal("2.01"))
    assert pb.state_subsidy + pb.centre_subsidy == pb.total_premium - pb.farmer_premium


def test_commercial_crop_5pct_farmer_share() -> None:
    nu05 = NotifiedUnit(
        unit_id="NU-05", district="G", block="M", crop="Cotton",
        crop_category=CropCategory.COMMERCIAL, season="KHARIF",
        risk_level=RiskLevel.MEDIUM, indemnity_level_pct=80,
        sum_insured_per_ha=Decimal("60000"), actuarial_rate_pct=Decimal("12"),
        normal_area_ha=Decimal("5200"), station_id="ST-03",
        normal_rain_jun_jul_mm=Decimal("380"), block_yield_kg_ha=1450,
    )
    pb = compute_premium(nu05, Decimal("1.24"))
    assert pb.sum_insured == Decimal("74400")
    assert pb.farmer_premium == Decimal("3720")   # 5% of SI


def test_rounding_half_up() -> None:
    # 52000 * 0.0001 = 5.2, rounded to 5
    nu = NotifiedUnit(
        unit_id="X", district="", block="", crop="",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.LOW, indemnity_level_pct=90,
        sum_insured_per_ha=Decimal("52000"), actuarial_rate_pct=Decimal("0.01"),
        normal_area_ha=Decimal("1"), station_id="ST-01",
        normal_rain_jun_jul_mm=Decimal("1"), block_yield_kg_ha=1,
    )
    pb = compute_premium(nu, Decimal("1.0"))
    # total = 52000 * 0.01% = 5.2 -> rounds to 5 (half-up on 5.2 -> 5)
    assert pb.total_premium == Decimal("5")
