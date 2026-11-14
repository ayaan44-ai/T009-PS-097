"""WeatherRepo — per-station rainfall + missing-day calendar.

Missing days are computed over the whole series 1 Jun – 30 Sep 2026
(locked decision L8). A date is 'missing' if no row exists in weather_daily
for that station on that date.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal

from src.config.constants import WEATHER_SERIES_END, WEATHER_SERIES_START
from src.util.dates import date_range_inclusive


class WeatherRepo:
    def __init__(self, rainfall: dict[str, dict[date, Decimal]]) -> None:
        self._rain = rainfall
        self._missing: dict[str, set[date]] = {}
        all_days = date_range_inclusive(WEATHER_SERIES_START, WEATHER_SERIES_END)
        for station, days in rainfall.items():
            self._missing[station] = set(all_days) - set(days.keys())

    def rain_for_date(self, station: str, d: date) -> Decimal | None:
        """Return rainfall or None if missing."""
        return self._rain.get(station, {}).get(d)

    def rain_series(self, station: str) -> dict[date, Decimal]:
        return dict(self._rain.get(station, {}))

    def missing_days(self, station: str) -> set[date]:
        return set(self._missing.get(station, set()))

    def missing_count(self, station: str) -> int:
        return len(self._missing.get(station, set()))

    def sum_rain_between(self, station: str, start: date, end: date) -> Decimal:
        """Sum rainfall in [start, end], treating missing days as 0 mm (L7)."""
        total = Decimal("0")
        cur = start
        while cur <= end:
            r = self.rain_for_date(station, cur)
            if r is not None:
                total += r
            cur = date.fromordinal(cur.toordinal() + 1)
        return total
