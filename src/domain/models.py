"""Plain data classes for PS-097. Masters frozen, transactional mutable."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from src.config.enums import (
    AccountStatus, ClaimStatus, ClaimType, CropCategory, DisbStatus,
    EnrolmentStatus, RiskLevel,
)

@dataclass(frozen=True)
class Station:
    station_id: str
    station_name: str
    district: str

@dataclass(frozen=True)
class NotifiedUnit:
    unit_id: str
    district: str
    block: str
    crop: str
    crop_category: CropCategory
    season: str
    risk_level: RiskLevel
    indemnity_level_pct: int
    sum_insured_per_ha: Decimal
    actuarial_rate_pct: Decimal
    normal_area_ha: Decimal
    station_id: str
    normal_rain_jun_jul_mm: Decimal
    block_yield_kg_ha: int

@dataclass(frozen=True)
class Farmer:
    farmer_id: str
    farmer_name: str
    gender: str
    village: str
    mobile: str
    bank_account: str
    ifsc: str
    account_status: AccountStatus

@dataclass(frozen=True)
class LandRecord:
    survey_no: str
    farmer_id: str
    village: str
    unit_id: str
    area_ha: Decimal

@dataclass(frozen=True)
class YieldHistory:
    unit_id: str
    year: int
    yield_kg_ha: int

@dataclass(frozen=True)
class CCEYield:
    cce_id: str
    unit_id: str
    survey_no: str
    experiment_date: date
    yield_kg_ha: int

@dataclass(frozen=True)
class SowingReport:
    report_id: str
    unit_id: str
    report_date: date
    area_sown_ha: Decimal

@dataclass
class Enrolment:
    enrolment_id: str
    farmer_id: str
    unit_id: str
    survey_no: str
    area_insured_ha: Decimal
    sum_insured: Decimal
    total_premium: Decimal
    farmer_premium: Decimal
    state_subsidy: Decimal
    centre_subsidy: Decimal
    status: EnrolmentStatus
    created_date: date

@dataclass
class Claim:
    unit_id: str
    farmer_id: str
    claim_type: ClaimType
    trigger_band: str
    gross_amount: Decimal
    cap_reduction: Decimal = Decimal("0")
    offset_reduction: Decimal = Decimal("0")
    net_amount: Decimal = Decimal("0")
    status: ClaimStatus = ClaimStatus.PENDING
    rule_id: str = ""
    finalisation_date: date | None = None
    created_date: date | None = None

@dataclass
class Disbursement:
    unit_id: str
    farmer_id: str
    claim_type: ClaimType
    net_amount: Decimal
    finalisation_date: date | None
    payment_date: date
    delay_days: int
    interest: Decimal
    total_paid: Decimal
    bank_account: str
    ifsc: str
    status: DisbStatus

@dataclass(frozen=True)
class CalamityNotification:
    notification_id: str
    farmer_id: str
    unit_id: str
    event_type: str
    event_ts: datetime
    notify_ts: datetime
    area_affected_ha: Decimal

@dataclass(frozen=True)
class Assessment:
    notification_id: str
    loss_pct: Decimal
    assess_date: date
