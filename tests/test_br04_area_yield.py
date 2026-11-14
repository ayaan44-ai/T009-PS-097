"""BR-04 area-yield claim — CCE mean, block-yield fallback, haircut."""
from datetime import date
from decimal import Decimal

from src.domain.models import CCEYield, Enrolment, NotifiedUnit
from src.config.enums import CropCategory, EnrolmentStatus, RiskLevel
from src.rules.br04_area_yield import actual_yield, area_yield_claim


def _unit_nu04() -> NotifiedUnit:
    return NotifiedUnit(
        unit_id="NU-04", district="H", block="Hir", crop="Ragi",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.HIGH, indemnity_level_pct=70,
        sum_insured_per_ha=Decimal("30000"), actuarial_rate_pct=Decimal("14"),
        normal_area_ha=Decimal("2800"), station_id="ST-02",
        normal_rain_jun_jul_mm=Decimal("520"), block_yield_kg_ha=1850,
    )


def _unit_nu02() -> NotifiedUnit:
    return NotifiedUnit(
        unit_id="NU-02", district="D", block="Nav", crop="Maize",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.MEDIUM, indemnity_level_pct=80,
        sum_insured_per_ha=Decimal("38000"), actuarial_rate_pct=Decimal("10.5"),
        normal_area_ha=Decimal("6100"), station_id="ST-01",
        normal_rain_jun_jul_mm=Decimal("560"), block_yield_kg_ha=3900,
    )


def _enrolment(unit_id: str, area: Decimal, si: Decimal) -> Enrolment:
    return Enrolment(
        enrolment_id="X", farmer_id="F", unit_id=unit_id, survey_no="SVY-X",
        area_insured_ha=area, sum_insured=si, total_premium=Decimal("0"),
        farmer_premium=Decimal("0"), state_subsidy=Decimal("0"),
        centre_subsidy=Decimal("0"), status=EnrolmentStatus.ACTIVE,
        created_date=date(2026, 7, 1),
    )


def test_ec04_exactly_4_cces_uses_mean_no_haircut() -> None:
    """EC-04: exactly 4 CCEs -> mean, used_block=False."""
    unit = _unit_nu02()
    cces = [
        CCEYield("C1", "NU-02", "S1", date(2026, 10, 1), 1395),
        CCEYield("C2", "NU-02", "S2", date(2026, 10, 1), 1460),
        CCEYield("C3", "NU-02", "S3", date(2026, 10, 1), 1361),
        CCEYield("C4", "NU-02", "S4", date(2026, 10, 1), 1345),
    ]
    actual, used_block = actual_yield(unit, cces)
    assert actual == Decimal("1390.25")
    assert used_block is False


def test_fewer_than_4_cces_uses_block_yield() -> None:
    unit = _unit_nu04()
    cces = [
        CCEYield("C1", "NU-04", "S1", date(2026, 10, 1), 1102),
        CCEYield("C2", "NU-04", "S2", date(2026, 10, 1), 1158),
        CCEYield("C3", "NU-04", "S3", date(2026, 10, 1), 1098),
    ]
    actual, used_block = actual_yield(unit, cces)
    assert actual == Decimal("1850")
    assert used_block is True


def test_no_shortfall_returns_none() -> None:
    unit = _unit_nu04()
    # threshold 1592.78, actual 1850 -> no shortfall
    cces = [CCEYield("C1", "NU-04", "S1", date(2026, 10, 1), 1102),
            CCEYield("C2", "NU-04", "S2", date(2026, 10, 1), 1158),
            CCEYield("C3", "NU-04", "S3", date(2026, 10, 1), 1098)]
    enr = _enrolment("NU-04", Decimal("1.77"), Decimal("53100"))
    assert area_yield_claim(enr, unit, Decimal("1592.78"), cces, date(2026, 10, 22)) is None


def test_nu02_claim_30151() -> None:
    """From dev: NU-02 area-yield claim = 30152."""
    unit = _unit_nu02()
    cces = [
        CCEYield("C1", "NU-02", "S1", date(2026, 10, 1), 1395),
        CCEYield("C2", "NU-02", "S2", date(2026, 10, 1), 1460),
        CCEYield("C3", "NU-02", "S3", date(2026, 10, 1), 1361),
        CCEYield("C4", "NU-02", "S4", date(2026, 10, 1), 1345),
    ]
    enr = _enrolment("NU-02", Decimal("1.30"), Decimal("49400"))
    claim = area_yield_claim(enr, unit, Decimal("3568.00"), cces, date(2026, 10, 20))
    assert claim is not None
    assert claim.gross_amount == Decimal("30152")


def test_10pct_haircut_on_block_yield_path() -> None:
    """When <4 CCEs and shortfall exists, gross is multiplied by 0.9."""
    unit = _unit_nu04()
    # Force a shortfall by using a very high threshold
    cces = [CCEYield("C1", "NU-04", "S1", date(2026, 10, 1), 1102)]
    enr = _enrolment("NU-04", Decimal("1.0"), Decimal("30000"))
    # threshold 5000, actual 1850 (block yield)
    claim = area_yield_claim(enr, unit, Decimal("5000"), cces, date(2026, 10, 1))
    assert claim is not None
    # Without haircut: (5000-1850)/5000 * 30000 * 1.0 = 18900
    # With 10% haircut:  18900 * 0.9 = 17010
    assert claim.gross_amount == Decimal("17010")
