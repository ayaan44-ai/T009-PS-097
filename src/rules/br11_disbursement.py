"""BR-11 — Disbursement rows with delay interest.

Rules:
- A claim is payable within 30 days of finalisation (inclusive).
- delay_days = max(0, payment_date - finalisation_date - 30)
- interest   = net_amount × 12% × delay_days / 365, rounded to rupee
- INACTIVE bank account → status HELD, interest = 0, total_paid = net_amount
- ACTIVE bank account   → status PAID, interest as computed

Locked decisions:
- L10: localised claims use the unit's FINALISE_YIELD date (passed in as
  unit_finalise_date). If None, delay_days = 0 (no interest).
- L13: caller controls which claims are included (approved and unpaid as of
  payment_date).
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal

from src.config.constants import DELAY_INTEREST_RATE_PCT, PAYMENT_WINDOW_DAYS
from src.config.enums import AccountStatus, DisbStatus
from src.domain.models import Claim, Disbursement, Farmer
from src.util.money import round_rupee


def delay_days_for(
    finalisation_date: date | None,
    payment_date: date,
) -> int:
    """Calendar days past the 30-day payment window. 0 if within or unknown."""
    if finalisation_date is None:
        return 0
    delta = (payment_date - finalisation_date).days - PAYMENT_WINDOW_DAYS
    return max(0, delta)


def interest_for(net_amount: Decimal, delay_days: int) -> Decimal:
    """Interest at 12% p.a. on net amount for given delay days, rounded."""
    if delay_days <= 0:
        return Decimal("0")
    return round_rupee(
        net_amount * DELAY_INTEREST_RATE_PCT * delay_days
        / (Decimal("100") * Decimal("365"))
    )


def disbursement_rows_for_unit(
    unit_id: str,
    payment_date: date,
    claims: list[Claim],
    farmers: dict[str, Farmer],
    already_paid_keys: set[tuple[str, str, str]],
    unit_finalise_date: date | None,
) -> list[Disbursement]:
    """Build disbursement rows for one unit on one payment_date.

    'claims' should be all claims for the unit. 'already_paid_keys' holds
    (unit_id, farmer_id, claim_type) triples already disbursed — those are skipped.
    """
    rows: list[Disbursement] = []
    for c in claims:
        if c.unit_id != unit_id:
            continue
        if c.net_amount <= Decimal("0"):
            continue
        key = (c.unit_id, c.farmer_id, c.claim_type.value)
        if key in already_paid_keys:
            continue
        farmer = farmers.get(c.farmer_id)
        if farmer is None:
            continue
        finalise = c.finalisation_date or unit_finalise_date
        days = delay_days_for(finalise, payment_date)
        if farmer.account_status == AccountStatus.INACTIVE:
            interest = Decimal("0")
            status = DisbStatus.HELD
        else:
            interest = interest_for(c.net_amount, days)
            status = DisbStatus.PAID
        total = c.net_amount + interest
        rows.append(Disbursement(
            unit_id=c.unit_id,
            farmer_id=c.farmer_id,
            claim_type=c.claim_type,
            net_amount=c.net_amount,
            finalisation_date=finalise,
            payment_date=payment_date,
            delay_days=days,
            interest=interest,
            total_paid=total,
            bank_account=farmer.bank_account,
            ifsc=farmer.ifsc,
            status=status,
        ))
    return rows
