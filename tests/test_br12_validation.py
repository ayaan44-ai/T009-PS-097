"""BR-12 duplicate survey + area cap."""
from datetime import date
from decimal import Decimal

from src.domain.models import Enrolment
from src.config.enums import EnrolmentStatus
from src.rules.br12_validation import find_duplicate_survey, cap_area


def _enr(enr_id: str, farmer: str, unit: str, survey: str) -> Enrolment:
    return Enrolment(
        enrolment_id=enr_id, farmer_id=farmer, unit_id=unit, survey_no=survey,
        area_insured_ha=Decimal("1.0"), sum_insured=Decimal("50000"),
        total_premium=Decimal("4500"), farmer_premium=Decimal("1000"),
        state_subsidy=Decimal("1750"), centre_subsidy=Decimal("1750"),
        status=EnrolmentStatus.ACTIVE, created_date=date(2026, 7, 1),
    )


def test_cross_unit_duplicate_rejected() -> None:
    """FMR-0006 tries SVY-0006 in NU-01 then NU-02 -> second rejected."""
    existing = [_enr("ENR-1", "FMR-0006", "NU-01", "SVY-0006")]
    dup = find_duplicate_survey(existing, "FMR-0006", "SVY-0006")
    assert dup is not None


def test_same_unit_duplicate_rejected() -> None:
    """Same survey, same unit, twice -> also rejected (L11)."""
    existing = [_enr("ENR-1", "FMR-0006", "NU-01", "SVY-0006")]
    dup = find_duplicate_survey(existing, "FMR-0006", "SVY-0006")
    assert dup is not None


def test_different_survey_ok() -> None:
    existing = [_enr("ENR-1", "FMR-0006", "NU-01", "SVY-0006")]
    assert find_duplicate_survey(existing, "FMR-0006", "SVY-0007") is None


def test_different_farmer_same_survey_ok() -> None:
    """A different farmer can enrol the same survey (edge — in practice survey has 1 owner)."""
    existing = [_enr("ENR-1", "FMR-0006", "NU-01", "SVY-0006")]
    assert find_duplicate_survey(existing, "FMR-0007", "SVY-0006") is None


def test_cap_area_when_claimed_larger() -> None:
    assert cap_area(Decimal("1.17"), Decimal("0.82")) == Decimal("0.82")


def test_cap_area_when_claimed_smaller() -> None:
    assert cap_area(Decimal("0.50"), Decimal("0.82")) == Decimal("0.50")


def test_cap_area_when_equal() -> None:
    assert cap_area(Decimal("0.82"), Decimal("0.82")) == Decimal("0.82")
