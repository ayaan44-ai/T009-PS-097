"""EnrolmentRepo — tracks accepted and rejected enrolments."""
from __future__ import annotations
from dataclasses import dataclass, field

from src.domain.models import Enrolment


@dataclass
class EnrolmentRepo:
    accepted: list[Enrolment] = field(default_factory=list)
    rejected: list[Enrolment] = field(default_factory=list)

    def add_accepted(self, e: Enrolment) -> None:
        self.accepted.append(e)

    def add_rejected(self, e: Enrolment) -> None:
        self.rejected.append(e)

    def active_for_unit(self, unit_id: str) -> list[Enrolment]:
        return [e for e in self.accepted if e.unit_id == unit_id]

    def all_active(self) -> list[Enrolment]:
        return list(self.accepted)

    def find_by_farmer_survey(self, farmer_id: str, survey_no: str) -> Enrolment | None:
        for e in self.accepted:
            if e.farmer_id == farmer_id and e.survey_no == survey_no:
                return e
        return None

    def find_active_for_farmer(self, farmer_id: str) -> list[Enrolment]:
        return [e for e in self.accepted if e.farmer_id == farmer_id]
