"""One dataclass per command verb. Parsed from commands.txt."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class EnrolCommand:
    enrolment_id: str
    farmer_id: str
    unit_id: str
    survey_no: str
    area_sown_ha: Decimal
    file_date: date


@dataclass(frozen=True)
class BankEnrolCommand:
    enrolment_id: str
    farmer_id: str
    unit_id: str
    survey_no: str
    area_sown_ha: Decimal
    file_date: date


@dataclass(frozen=True)
class OptOutCommand:
    farmer_id: str
    unit_id: str
    request_date: date


@dataclass(frozen=True)
class EvalWeatherCommand:
    unit_id: str
    trigger: str
    eval_date: date


@dataclass(frozen=True)
class EvalSowingCommand:
    unit_id: str
    eval_date: date


@dataclass(frozen=True)
class CalamityCommand:
    notification_id: str
    farmer_id: str
    unit_id: str
    event_type: str
    event_ts: datetime
    notify_ts: datetime
    area_affected_ha: Decimal


@dataclass(frozen=True)
class AssessCommand:
    notification_id: str
    loss_pct: Decimal
    assess_date: date


@dataclass(frozen=True)
class FinaliseYieldCommand:
    unit_id: str
    finalise_date: date


@dataclass(frozen=True)
class DisburseCommand:
    unit_id: str
    payment_date: date


@dataclass(frozen=True)
class PrintPremiumCommand:
    unit_id: str


@dataclass(frozen=True)
class PrintClaimsCommand:
    unit_id: str


@dataclass(frozen=True)
class PrintDisbursementCommand:
    as_of_date: date
