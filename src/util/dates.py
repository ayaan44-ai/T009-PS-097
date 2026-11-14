"""Date helpers. All dates naive (no timezone) per README."""
from __future__ import annotations
from datetime import date, datetime

DATE_FMT = "%Y-%m-%d"
TS_FMT = "%Y-%m-%d %H:%M:%S"

def parse_date(s: str) -> date:
    return datetime.strptime(s.strip(), DATE_FMT).date()

def parse_timestamp(s: str) -> datetime:
    return datetime.strptime(s.strip(), TS_FMT)

def days_between(a: date, b: date) -> int:
    return (b - a).days

def date_range_inclusive(start: date, end: date) -> list[date]:
    out = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur = date.fromordinal(cur.toordinal() + 1)
    return out
