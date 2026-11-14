"""BR-09 — Localised calamity (hailstorm / inundation).

Rules:
- Farmer must notify within 72 hours of event (inclusive).
- Late notifications are REJECTED.
- payout = loss_pct/100 × SI/ha × min(area_affected, enrolled_area)
- (localised_net + weather_already_paid) <= 50% of SI (locked decision L2 for cap basis)
- Prior weather payouts for the same (farmer, unit) reduce the localised headroom.

The 'weather_already_paid' input is the sum of net amounts of approved
deficit/dry/excess claims for this farmer+unit so far.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal

from src.config.constants import (
    LOCALISED_NOTIFY_WINDOW_HOURS,
    LOCALISED_PLUS_WEATHER_CAP_PCT,
)
from src.config.enums import ClaimStatus, ClaimType
from src.domain.models import (
    Assessment,
    CalamityNotification,
    Claim,
    Enrolment,
    NotifiedUnit,
)
from src.util.money import round_rupee


def is_notification_on_time(
    notification: CalamityNotification,
) -> bool:
    """True if notified within 72 hours of event (inclusive)."""
    delta_hours = (notification.notify_ts - notification.event_ts).total_seconds() / 3600
    return delta_hours <= LOCALISED_NOTIFY_WINDOW_HOURS


def localised_claim(
    notification: CalamityNotification,
    assessment: Assessment,
    enrolment: Enrolment,
    unit: NotifiedUnit,
    weather_already_paid: Decimal,
    finalise_date: date,
) -> Claim | None:
    """Compute the localised claim, or None if rejected or zero amount."""
    if not is_notification_on_time(notification):
        return None   # rejected; caller should not emit a row

    # Area cap: min(claimed, enrolled)
    affected = min(notification.area_affected_ha, enrolment.area_insured_ha)

    # Gross before 50% cap
    gross = round_rupee(
        (assessment.loss_pct / Decimal("100"))
        * unit.sum_insured_per_ha
        * affected
    )
    if gross <= Decimal("0"):
        return None

    # 50% localised+weather cap on SI
    si = enrolment.sum_insured
    cap_50 = round_rupee(si * LOCALISED_PLUS_WEATHER_CAP_PCT / Decimal("100"))
    headroom = cap_50 - weather_already_paid
    if headroom < Decimal("0"):
        headroom = Decimal("0")
    net = min(gross, headroom)
    cap_reduction = gross - net

    if net <= Decimal("0"):
        return None

    return Claim(
        unit_id=enrolment.unit_id,
        farmer_id=enrolment.farmer_id,
        claim_type=ClaimType.LOCALISED,
        trigger_band=f"{assessment.loss_pct}%",
        gross_amount=gross,
        cap_reduction=cap_reduction,
        offset_reduction=Decimal("0"),
        net_amount=net,
        status=ClaimStatus.PENDING,
        rule_id="BR-09",
        finalisation_date=finalise_date,
        created_date=assessment.assess_date,
    )
