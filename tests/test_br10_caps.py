"""BR-10 claim caps, offset, no-double-indemnity."""
from datetime import date
from decimal import Decimal

from src.domain.models import Claim, Enrolment
from src.config.enums import ClaimType, ClaimStatus, EnrolmentStatus
from src.rules.br10_caps import apply_caps


def _enr(si: Decimal) -> Enrolment:
    return Enrolment(
        enrolment_id="X", farmer_id="F", unit_id="NU-01", survey_no="SVY-X",
        area_insured_ha=Decimal("1.5"), sum_insured=si,
        total_premium=Decimal("0"), farmer_premium=Decimal("0"),
        state_subsidy=Decimal("0"), centre_subsidy=Decimal("0"),
        status=EnrolmentStatus.ACTIVE, created_date=date(2026, 7, 1),
    )


def _claim(ct: ClaimType, gross: Decimal, net: Decimal | None = None) -> Claim:
    return Claim(
        unit_id="NU-01", farmer_id="F", claim_type=ct, trigger_band="X",
        gross_amount=gross, net_amount=net if net is not None else gross,
        status=ClaimStatus.PENDING,
    )


def test_ec08_area_yield_fully_offset() -> None:
    """EC-08: area-yield 9360 fully offset by 19500 weather -> net 0."""
    enr = _enr(Decimal("78000"))
    prior = [_claim(ClaimType.DRY_SPELL, Decimal("19500"))]
    ay = _claim(ClaimType.AREA_YIELD, Decimal("9360"))
    result = apply_caps(ay, enr, prior)
    assert result.offset_reduction == Decimal("9360")
    assert result.net_amount == Decimal("0")


def test_area_yield_partial_offset() -> None:
    """Area-yield 40000 minus weather 20000 = 20000 net."""
    enr = _enr(Decimal("78000"))
    prior = [_claim(ClaimType.DEFICIT_RAIN, Decimal("20000"))]
    ay = _claim(ClaimType.AREA_YIELD, Decimal("40000"))
    result = apply_caps(ay, enr, prior)
    assert result.offset_reduction == Decimal("20000")
    assert result.net_amount == Decimal("20000")


def test_100pct_cap_on_weather() -> None:
    """Prior 60% SI paid + new 60% SI claim -> capped at remaining 40% SI."""
    enr = _enr(Decimal("78000"))
    prior = [_claim(ClaimType.DEFICIT_RAIN, Decimal("46800"))]    # 60% SI
    new = _claim(ClaimType.DRY_SPELL, Decimal("46800"))            # another 60% SI
    result = apply_caps(new, enr, prior)
    # room = 78000 - 46800 = 31200
    assert result.net_amount == Decimal("31200")
    assert result.cap_reduction == Decimal("15600")


def test_clean_area_yield_no_offset() -> None:
    """Isolated area-yield: no prior claims -> no offset, no cap."""
    enr = _enr(Decimal("78000"))
    ay = _claim(ClaimType.AREA_YIELD, Decimal("3900"))
    result = apply_caps(ay, enr, [])
    assert result.offset_reduction == Decimal("0")
    assert result.net_amount == Decimal("3900")


def test_total_never_exceeds_si() -> None:
    """Three claims each 50% SI: total should be capped at 100% SI."""
    enr = _enr(Decimal("100000"))
    prior = [
        _claim(ClaimType.DEFICIT_RAIN, Decimal("50000")),
        _claim(ClaimType.DRY_SPELL, Decimal("50000")),
    ]
    new = _claim(ClaimType.EXCESS_RAIN, Decimal("50000"))
    result = apply_caps(new, enr, prior)
    # prior_net = 100000, room = 0 -> new net = 0
    assert result.net_amount == Decimal("0")
