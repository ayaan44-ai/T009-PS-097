"""BR-08 prevented sowing — strict <, exact boundary, claim amount."""
from datetime import date
from decimal import Decimal

from src.domain.models import Enrolment, NotifiedUnit, SowingReport
from src.config.enums import CropCategory, EnrolmentStatus, RiskLevel
from src.rules.br08_prevented import is_prevented, prevented_claim


def _nu06() -> NotifiedUnit:
    return NotifiedUnit(
        unit_id="NU-06", district="G", block="R", crop="Tur",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.HIGH, indemnity_level_pct=70,
        sum_insured_per_ha=Decimal("34000"), actuarial_rate_pct=Decimal("15"),
        normal_area_ha=Decimal("3900"), station_id="ST-03",
        normal_rain_jun_jul_mm=Decimal("540"), block_yield_kg_ha=780,
    )


def test_ec05_nu06_prevented() -> None:
    """EC-05: NU-06 has 858 ha sown, 25% of 3900 = 975 -> prevented."""
    report = SowingReport("SOW-018", "NU-06", date(2026, 8, 15), Decimal("858"))
    assert is_prevented(report, _nu06()) is True


def test_exactly_25pct_not_prevented() -> None:
    """Exactly 975 = 25% -> not prevented (strict <)."""
    report = SowingReport("SOW-X", "NU-06", date(2026, 8, 15), Decimal("975"))
    assert is_prevented(report, _nu06()) is False


def test_974_99_prevented() -> None:
    report = SowingReport("SOW-Y", "NU-06", date(2026, 8, 15), Decimal("974.99"))
    assert is_prevented(report, _nu06()) is True


def test_fully_sown_not_prevented() -> None:
    report = SowingReport("SOW-Z", "NU-06", date(2026, 8, 15), Decimal("3900"))
    assert is_prevented(report, _nu06()) is False


def test_prevented_claim_amount_is_25pct_of_si() -> None:
    """FMR-0133 enrolled 0.74 ha, SI 25160. 25% = 6290."""
    enr = Enrolment(
        enrolment_id="ENR-0008", farmer_id="FMR-0133", unit_id="NU-06",
        survey_no="SVY-0133", area_insured_ha=Decimal("0.74"),
        sum_insured=Decimal("25160"), total_premium=Decimal("3774"),
        farmer_premium=Decimal("503"), state_subsidy=Decimal("1636"),
        centre_subsidy=Decimal("1635"), status=EnrolmentStatus.ACTIVE,
        created_date=date(2026, 6, 22),
    )
    claim = prevented_claim(enr, _nu06(), date(2026, 8, 16))
    assert claim.gross_amount == Decimal("6290")
    assert claim.trigger_band == "25%"
    assert claim.rule_id == "BR-08"
