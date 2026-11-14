"""All magic numbers for PS-097, tagged by BR."""
from __future__ import annotations
from datetime import date
from decimal import Decimal

SEASON_NAME = "KHARIF"
SEASON_YEAR = 2026
ENROLMENT_CUTOFF = date(2026, 7, 31)
OPT_OUT_CUTOFF = date(2026, 7, 24)
SOWING_REPORT_EVAL_DATE = date(2026, 8, 15)
PAYMENT_WINDOW_DAYS = 30

WEATHER_SERIES_START = date(2026, 6, 1)
WEATHER_SERIES_END = date(2026, 9, 30)
DEFICIT_WINDOW_START = date(2026, 6, 1)
DEFICIT_WINDOW_END = date(2026, 7, 31)
DRY_EXCESS_WINDOW_START = date(2026, 7, 1)
DRY_EXCESS_WINDOW_END = date(2026, 9, 30)

FARMER_SHARE_PCT = {
    ("KHARIF", "FOOD"): Decimal("2.0"),
    ("KHARIF", "COMMERCIAL"): Decimal("5.0"),
    ("RABI", "FOOD"): Decimal("1.5"),
    ("RABI", "COMMERCIAL"): Decimal("5.0"),
}

YIELD_HISTORY_YEARS = 7
BEST_N_YEARS = 5

MIN_CCES = 4
BLOCK_YIELD_HAIRCUT = Decimal("0.90")

DEFICIT_BANDS = [
    (Decimal("40"), Decimal("60"), "60%"),
    (Decimal("60"), Decimal("40"), "40%"),
    (Decimal("75"), Decimal("20"), "20%"),
]

DRY_DAY_THRESHOLD_MM = Decimal("2.5")
MIN_DRY_SPELL_DAYS = 20
DRY_SPELL_FIRST_PCT = Decimal("15.0")
DRY_SPELL_SECOND_PCT = Decimal("10.0")
DRY_SPELL_CAP_PCT = Decimal("25.0")

EXCESS_WINDOW_DAYS = 3
EXCESS_THRESHOLD_MM = Decimal("200")
EXCESS_PAYOUT_PCT = Decimal("15.0")
MISSING_DAY_LIMIT = 10
REPLACEMENT_MAX_KM = Decimal("25.0")

PREVENTED_SOWN_FRACTION = Decimal("0.25")
PREVENTED_PAYOUT_PCT = Decimal("25.0")

LOCALISED_NOTIFY_WINDOW_HOURS = 72
LOCALISED_PLUS_WEATHER_CAP_PCT = Decimal("50.0")

TOTAL_CAP_PCT = Decimal("100.0")
DELAY_INTEREST_RATE_PCT = Decimal("12.0")
MONEY_QUANTUM = Decimal("1")
