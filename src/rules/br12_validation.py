"""BR-12 — Duplicate survey prevention + area cap.

Two responsibilities:
1. At enrolment: reject if (farmer_id, survey_no) is already active in any unit.
   Locked decision L11: same unit twice is also rejected.
2. At claim: cap claimed/affected area to enrolled area.

This module exposes pure helpers; the engine (handlers.py) wires them
against EnrolmentRepo at command time.
"""
from __future__ import annotations
from decimal import Decimal

from src.domain.models import Enrolment


def find_duplicate_survey(
    existing_enrolments: list[Enrolment],
    farmer_id: str,
    survey_no: str,
) -> Enrolment | None:
    """Return the existing active enrolment if (farmer, survey) already enrolled."""
    for e in existing_enrolments:
        if e.farmer_id == farmer_id and e.survey_no == survey_no:
            return e
    return None


def cap_area(affected_ha: Decimal, enrolled_ha: Decimal) -> Decimal:
    """Return the smaller of the two — for claim areas."""
    return min(affected_ha, enrolled_ha)
