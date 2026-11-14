"""MasterRepo — read-only in-memory index of all master data."""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.models import (
    CCEYield, Farmer, LandRecord, NotifiedUnit, SowingReport, Station, YieldHistory,
)


@dataclass
class MasterRepo:
    stations: dict[str, Station] = field(default_factory=dict)
    distances: dict[tuple[str, str], Decimal] = field(default_factory=dict)
    units: dict[str, NotifiedUnit] = field(default_factory=dict)
    farmers: dict[str, Farmer] = field(default_factory=dict)
    land: dict[str, LandRecord] = field(default_factory=dict)
    yields: dict[str, list[YieldHistory]] = field(default_factory=dict)
    cces: dict[str, list[CCEYield]] = field(default_factory=dict)
    sowing: dict[str, list[SowingReport]] = field(default_factory=dict)

    def unit(self, unit_id: str) -> NotifiedUnit:
        return self.units[unit_id]

    def farmer(self, farmer_id: str) -> Farmer:
        return self.farmers[farmer_id]

    def land_record(self, survey_no: str) -> LandRecord:
        return self.land[survey_no]

    def yields_for(self, unit_id: str) -> list[YieldHistory]:
        return self.yields.get(unit_id, [])

    def cces_for(self, unit_id: str) -> list[CCEYield]:
        return self.cces.get(unit_id, [])

    def sowing_for(self, unit_id: str) -> list[SowingReport]:
        return self.sowing.get(unit_id, [])

    def station_distance(self, a: str, b: str) -> Decimal | None:
        key = (a, b) if a < b else (b, a)
        return self.distances.get(key)
