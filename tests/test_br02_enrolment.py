"""BR-02 enrolment cut-off, opt-out window, area cap."""
from datetime import date
from decimal import Decimal
from src.domain.models import LandRecord
from src.rules.br02_enrolment import (
    validate_enrolment_date, validate_opt_out_date, validate_area,
)


def _land() -> LandRecord:
    return LandRecord(
        survey_no="SVY-0005", farmer_id="FMR-0005", village="Dum",
        unit_id="NU-01", area_ha=Decimal("3.88"),
    )


def test_enrolment_cutoff_inclusive() -> None:
    assert validate_enrolment_date(date(2026, 7, 31)).ok is True
    assert validate_enrolment_date(date(2026, 8, 1)).ok is False


def test_opt_out_cutoff_inclusive() -> None:
    assert validate_opt_out_date(date(2026, 7, 24)).ok is True
    assert validate_opt_out_date(date(2026, 7, 25)).ok is False


def test_area_at_limit_ok() -> None:
    assert validate_area(Decimal("3.88"), _land()).ok is True


def test_area_over_limit_rejected() -> None:
    v = validate_area(Decimal("4.08"), _land())
    assert v.ok is False
    assert v.reason == "AREA_EXCEEDS_LAND"


def test_area_below_limit_ok() -> None:
    assert validate_area(Decimal("0.50"), _land()).ok is True
