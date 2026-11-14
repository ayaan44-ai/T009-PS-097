"""BR-11 delay interest + HELD status."""
from datetime import date
from decimal import Decimal

from src.domain.models import Claim, Farmer
from src.config.enums import AccountStatus, ClaimType, DisbStatus
from src.rules.br11_disbursement import (
    delay_days_for, interest_for, disbursement_rows_for_unit,
)


def _farmer(status: AccountStatus) -> Farmer:
    return Farmer(
        farmer_id="F", farmer_name="N", gender="M", village="V",
        mobile="9999999999", bank_account="12345678901",
        ifsc="AAAA0123456", account_status=status,
    )


def _claim(ct: ClaimType, net: Decimal, finalise: date) -> Claim:
    return Claim(
        unit_id="NU-01", farmer_id="F", claim_type=ct, trigger_band="X",
        gross_amount=net, net_amount=net, finalisation_date=finalise,
    )


def test_30_days_exactly_no_interest() -> None:
    """NU-01: 20 Oct -> 19 Nov = 30 days -> 0 interest."""
    assert delay_days_for(date(2026, 10, 20), date(2026, 11, 19)) == 0


def test_31_days_one_day_interest() -> None:
    assert delay_days_for(date(2026, 10, 20), date(2026, 11, 20)) == 1


def test_45_days_15_delay() -> None:
    """NU-02: 20 Oct -> 4 Dec = 45 days -> 15 delay."""
    assert delay_days_for(date(2026, 10, 20), date(2026, 12, 4)) == 15


def test_interest_calculation() -> None:
    """100000 × 12% × 15/365 = 493.15 -> 493."""
    assert interest_for(Decimal("100000"), 15) == Decimal("493")


def test_active_farmer_gets_paid() -> None:
    claim = _claim(ClaimType.AREA_YIELD, Decimal("50000"), date(2026, 10, 20))
    rows = disbursement_rows_for_unit(
        "NU-01", date(2026, 12, 4), [claim],
        {"F": _farmer(AccountStatus.ACTIVE)}, set(), date(2026, 10, 20),
    )
    assert len(rows) == 1
    r = rows[0]
    assert r.delay_days == 15
    assert r.interest == Decimal("247")
    assert r.total_paid == Decimal("50247")
    assert r.status == DisbStatus.PAID


def test_inactive_farmer_held_no_interest() -> None:
    claim = _claim(ClaimType.AREA_YIELD, Decimal("50000"), date(2026, 10, 20))
    rows = disbursement_rows_for_unit(
        "NU-01", date(2026, 12, 4), [claim],
        {"F": _farmer(AccountStatus.INACTIVE)}, set(), date(2026, 10, 20),
    )
    r = rows[0]
    assert r.delay_days == 15    # days still computed
    assert r.interest == Decimal("0")
    assert r.total_paid == Decimal("50000")
    assert r.status == DisbStatus.HELD


def test_already_paid_skipped() -> None:
    claim = _claim(ClaimType.AREA_YIELD, Decimal("50000"), date(2026, 10, 20))
    already = {("NU-01", "F", "AREA_YIELD")}
    rows = disbursement_rows_for_unit(
        "NU-01", date(2026, 12, 4), [claim],
        {"F": _farmer(AccountStatus.ACTIVE)}, already, date(2026, 10, 20),
    )
    assert len(rows) == 0
