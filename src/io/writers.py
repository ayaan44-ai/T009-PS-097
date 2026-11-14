"""CSV writers — the ONLY place that formats output rows.

Output files:
- premium_statement.csv
- claims.csv
- disbursement.csv

Formatting rules:
- dates: YYYY-MM-DD
- money: 2 decimal places, no commas, no symbols
- header row on every file
"""
from __future__ import annotations
import csv
from decimal import Decimal
from pathlib import Path

from src.domain.models import Claim, Disbursement, Enrolment
from src.util.money import rupee_str


PREMIUM_HEADERS = [
    "enrolment_id", "farmer_id", "unit_id", "survey_no", "area_insured_ha",
    "sum_insured", "total_premium", "farmer_premium", "state_subsidy",
    "centre_subsidy", "status",
]

CLAIMS_HEADERS = [
    "unit_id", "farmer_id", "claim_type", "trigger_band", "gross_amount",
    "cap_reduction", "offset_reduction", "net_amount", "status", "rule_id",
]

DISBURSEMENT_HEADERS = [
    "unit_id", "farmer_id", "claim_type", "net_amount", "finalisation_date",
    "payment_date", "delay_days", "interest", "total_paid", "bank_account",
    "ifsc", "status",
]


def _money(v: Decimal) -> str:
    return rupee_str(v)


def _area(v: Decimal) -> str:
    return f"{v:.2f}"


def write_premium_statement(path: Path, enrolments: list[Enrolment]) -> None:
    """One row per accepted enrolment, sorted by enrolment_id."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(PREMIUM_HEADERS)
        for e in sorted(enrolments, key=lambda x: x.enrolment_id):
            w.writerow([
                e.enrolment_id, e.farmer_id, e.unit_id, e.survey_no,
                _area(e.area_insured_ha), _money(e.sum_insured),
                _money(e.total_premium), _money(e.farmer_premium),
                _money(e.state_subsidy), _money(e.centre_subsidy),
                e.status.value,
            ])


def write_claims(path: Path, claims: list[Claim]) -> None:
    """One row per farmer per unit per claim type, sorted by (unit, farmer)."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CLAIMS_HEADERS)
        for c in sorted(claims, key=lambda x: (x.unit_id, x.farmer_id, x.claim_type.value)):
            w.writerow([
                c.unit_id, c.farmer_id, c.claim_type.value, c.trigger_band,
                _money(c.gross_amount), _money(c.cap_reduction),
                _money(c.offset_reduction), _money(c.net_amount),
                c.status.value, c.rule_id,
            ])


def write_disbursement(path: Path, rows: list[Disbursement]) -> None:
    """One row per payment line, sorted by payment_date (then unit, farmer)."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(DISBURSEMENT_HEADERS)
        for r in sorted(rows, key=lambda x: (x.payment_date, x.unit_id, x.farmer_id, x.claim_type.value)):
            w.writerow([
                r.unit_id, r.farmer_id, r.claim_type.value, _money(r.net_amount),
                r.finalisation_date.isoformat() if r.finalisation_date else "",
                r.payment_date.isoformat(), str(r.delay_days),
                _money(r.interest), _money(r.total_paid),
                r.bank_account, r.ifsc, r.status.value,
            ])
