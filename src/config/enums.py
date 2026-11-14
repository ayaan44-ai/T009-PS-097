"""Enumerations used across the engine."""
from __future__ import annotations
from enum import Enum

class CropCategory(str, Enum):
    FOOD = "FOOD"
    COMMERCIAL = "COMMERCIAL"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class EnrolmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    OPTED_OUT = "OPTED_OUT"

class UnitStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"

class ClaimType(str, Enum):
    AREA_YIELD = "AREA_YIELD"
    DEFICIT_RAIN = "DEFICIT_RAIN"
    DRY_SPELL = "DRY_SPELL"
    EXCESS_RAIN = "EXCESS_RAIN"
    PREVENTED_SOWING = "PREVENTED_SOWING"
    LOCALISED = "LOCALISED"

class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    HELD = "HELD"
    REJECTED = "REJECTED"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"
    TERMINATED = "TERMINATED"

class DisbStatus(str, Enum):
    PAID = "PAID"
    HELD = "HELD"

class TriggerType(str, Enum):
    DEFICIT_RAIN = "DEFICIT_RAIN"
    DRY_SPELL = "DRY_SPELL"
    EXCESS_RAIN = "EXCESS_RAIN"
