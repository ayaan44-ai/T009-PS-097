"""BR-10 — Claim precedence, caps, and no-double-indemnity.

Precedence rules:
1. Area-yield claim is reduced by the sum of approved weather + localised
   net amounts for the same (farmer, unit). This is the "no double indemnity"
   offset (locked decision L1: uses approved, not just disbursed).
2. Total net payout per farmer per season is capped at 100% of SI
   (locked decision L2: cap applied after offset).
3. Cap and offset are reported separately.

Order:
    raw_net       = gross - cap_reduction_already_applied_by_caller
    offset        = min(raw_net, prior_weather_and_localised)
    after_offset  = raw_net - offset
    cap_100       = 100% SI
    cap_reduction = max(0, (sum_all_net_for_this_farmer + after_offset) - cap_100)
    net           = after_offset - cap_reduction

For non-area-yield claims, the function also enforces the 100% cap
but does NOT apply offset (only area-yield is offset).

The function takes the full list of prior claims for this farmer+unit
to compute running total for the 100% cap.
"""
from __future__ import annotations
from decimal import Decimal

from src.config.constants import TOTAL_CAP_PCT
from src.config.enums import ClaimType
from src.domain.models import Claim, Enrolment
from src.util.money import round_rupee


def apply_caps(
    claim: Claim,
    enrolment: Enrolment,
    prior_claims: list[Claim],
) -> Claim:
    """Return a new Claim with cap_reduction, offset_reduction, net_amount set."""
    si = enrolment.sum_insured
    cap_100 = round_rupee(si * TOTAL_CAP_PCT / Decimal("100"))

    # Step 1: if this is AREA_YIELD, apply offset from prior weather + localised
    if claim.claim_type == ClaimType.AREA_YIELD:
        prior_offset_base = sum(
            (c.net_amount for c in prior_claims
             if c.claim_type in (ClaimType.DEFICIT_RAIN, ClaimType.DRY_SPELL,
                                 ClaimType.EXCESS_RAIN, ClaimType.LOCALISED)),
            Decimal("0"),
        )
        offset = min(claim.gross_amount, prior_offset_base)
        after_offset = claim.gross_amount - offset
    else:
        offset = Decimal("0")
        after_offset = claim.gross_amount

    # Step 2: 100% cap on total net for this farmer (including this claim)
    prior_net_sum = sum(
        (c.net_amount for c in prior_claims),
        Decimal("0"),
    )
    room = cap_100 - prior_net_sum
    if room < Decimal("0"):
        room = Decimal("0")
    net = min(after_offset, room)
    cap_reduction = after_offset - net

    return Claim(
        unit_id=claim.unit_id,
        farmer_id=claim.farmer_id,
        claim_type=claim.claim_type,
        trigger_band=claim.trigger_band,
        gross_amount=claim.gross_amount,
        cap_reduction=cap_reduction,
        offset_reduction=offset,
        net_amount=net,
        status=claim.status,
        rule_id=claim.rule_id,
        finalisation_date=claim.finalisation_date,
        created_date=claim.created_date,
    )
