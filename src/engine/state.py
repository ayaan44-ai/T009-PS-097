"""EngineState — single source of truth for the entire run."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.config.enums import ClaimType, UnitStatus
from src.domain.models import (
    Assessment, CalamityNotification, Claim, Disbursement,
)
from src.repository.enrolment_repo import EnrolmentRepo
from src.repository.master_repo import MasterRepo
from src.repository.weather_repo import WeatherRepo


@dataclass
class EngineState:
    masters: MasterRepo
    weather: WeatherRepo
    enrolments: EnrolmentRepo = field(default_factory=EnrolmentRepo)
    claims: dict[tuple[str, str], list[Claim]] = field(default_factory=dict)
    unit_status: dict[str, UnitStatus] = field(default_factory=dict)
    unit_finalise_date: dict[str, date] = field(default_factory=dict)
    paid_claim_keys: set[tuple[str, str, str]] = field(default_factory=set)
    disbursements: list[Disbursement] = field(default_factory=list)
    notifications: dict[str, CalamityNotification] = field(default_factory=dict)
    rejected_notifications: set[str] = field(default_factory=set)
    assessments: dict[str, Assessment] = field(default_factory=dict)

    def is_unit_terminated(self, unit_id: str) -> bool:
        return self.unit_status.get(unit_id) == UnitStatus.TERMINATED

    def terminate_unit(self, unit_id: str) -> None:
        self.unit_status[unit_id] = UnitStatus.TERMINATED

    def all_claims_for_unit(self, unit_id: str) -> list[Claim]:
        out: list[Claim] = []
        for (u, _f), claims in self.claims.items():
            if u == unit_id:
                out.extend(claims)
        return out

    def claims_for_farmer_unit(self, unit_id: str, farmer_id: str) -> list[Claim]:
        return list(self.claims.get((unit_id, farmer_id), []))

    def add_claim(self, claim: Claim) -> None:
        key = (claim.unit_id, claim.farmer_id)
        self.claims.setdefault(key, []).append(claim)

    def net_weather_paid_for_farmer(self, unit_id: str, farmer_id: str) -> Decimal:
        """Sum of net amounts of approved weather claims for this farmer+unit."""
        weather_types = {ClaimType.DEFICIT_RAIN, ClaimType.DRY_SPELL, ClaimType.EXCESS_RAIN}
        total = Decimal("0")
        for c in self.claims_for_farmer_unit(unit_id, farmer_id):
            if c.claim_type in weather_types:
                total += c.net_amount
        return total

    def net_localised_paid_for_farmer(self, unit_id: str, farmer_id: str) -> Decimal:
        total = Decimal("0")
        for c in self.claims_for_farmer_unit(unit_id, farmer_id):
            if c.claim_type == ClaimType.LOCALISED:
                total += c.net_amount
        return total
