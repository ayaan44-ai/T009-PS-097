"""BR-09 localised calamity — 72h boundary, area cap, 50% cap."""
from datetime import date, datetime
from decimal import Decimal

from src.domain.models import Assessment, CalamityNotification, Enrolment, NotifiedUnit
from src.config.enums import CropCategory, EnrolmentStatus, RiskLevel
from src.rules.br09_localised import is_notification_on_time, localised_claim


def _nu01() -> NotifiedUnit:
    return NotifiedUnit(
        unit_id="NU-01", district="D", block="K", crop="Paddy",
        crop_category=CropCategory.FOOD, season="KHARIF",
        risk_level=RiskLevel.LOW, indemnity_level_pct=90,
        sum_insured_per_ha=Decimal("52000"), actuarial_rate_pct=Decimal("9"),
        normal_area_ha=Decimal("4200"), station_id="ST-01",
        normal_rain_jun_jul_mm=Decimal("520"), block_yield_kg_ha=3650,
    )


def _enrolment(area: Decimal, si: Decimal) -> Enrolment:
    return Enrolment(
        enrolment_id="X", farmer_id="F", unit_id="NU-01", survey_no="SVY-X",
        area_insured_ha=area, sum_insured=si, total_premium=Decimal("0"),
        farmer_premium=Decimal("0"), state_subsidy=Decimal("0"),
        centre_subsidy=Decimal("0"), status=EnrolmentStatus.ACTIVE,
        created_date=date(2026, 7, 1),
    )


def test_ec06_72h_exactly_is_valid() -> None:
    """EC-06: 72 hours exactly -> on time."""
    n = CalamityNotification(
        "CAL-001", "FMR-0102", "NU-04", "INUNDATION",
        event_ts=datetime(2026, 8, 25, 18, 15, 0),
        notify_ts=datetime(2026, 8, 28, 18, 15, 0),   # 72h exactly
        area_affected_ha=Decimal("0.39"),
    )
    assert is_notification_on_time(n) is True


def test_72h_1min_is_late() -> None:
    n = CalamityNotification(
        "CAL-002", "FMR-0128", "NU-05", "INUNDATION",
        event_ts=datetime(2026, 8, 24, 17, 15, 0),
        notify_ts=datetime(2026, 8, 27, 17, 16, 0),   # 72h 1min
        area_affected_ha=Decimal("1.30"),
    )
    assert is_notification_on_time(n) is False


def test_claimed_area_capped_to_enrolled() -> None:
    """CAL-003: 1.17 ha claimed, 0.82 ha enrolled -> cap to 0.82."""
    n = CalamityNotification(
        "CAL-003", "FMR-0017", "NU-01", "HAILSTORM",
        event_ts=datetime(2026, 9, 5, 14, 45, 0),
        notify_ts=datetime(2026, 9, 7, 5, 45, 0),
        area_affected_ha=Decimal("1.17"),
    )
    a = Assessment("CAL-003", Decimal("55.0"), date(2026, 9, 15))
    enr = _enrolment(Decimal("0.82"), Decimal("42640"))
    claim = localised_claim(n, a, enr, _nu01(), Decimal("0"), date(2026, 9, 15))
    # 0.55 × 52000 × 0.82 = 23452
    assert claim.gross_amount == Decimal("23452")


def test_50pct_cap_with_prior_weather() -> None:
    """Weather already 20% SI paid, localised gross 40% SI -> net 30% SI."""
    n = CalamityNotification(
        "CAL-X", "F", "NU-01", "HAILSTORM",
        event_ts=datetime(2026, 8, 20, 10, 0, 0),
        notify_ts=datetime(2026, 8, 21, 10, 0, 0),
        area_affected_ha=Decimal("1.0"),
    )
    a = Assessment("CAL-X", Decimal("40.0"), date(2026, 8, 22))
    enr = _enrolment(Decimal("1.0"), Decimal("52000"))
    weather_paid = Decimal("10400")   # 20% of 52000
    claim = localised_claim(n, a, enr, _nu01(), weather_paid, date(2026, 8, 22))
    # cap_50 = 26000, headroom = 26000 - 10400 = 15600
    # gross = 40% × 52000 × 1.0 = 20800, net = min(20800, 15600) = 15600
    assert claim.gross_amount == Decimal("20800")
    assert claim.net_amount == Decimal("15600")
    assert claim.cap_reduction == Decimal("5200")


def test_late_notification_returns_none() -> None:
    n = CalamityNotification(
        "CAL-Y", "F", "NU-01", "HAILSTORM",
        event_ts=datetime(2026, 8, 20, 10, 0, 0),
        notify_ts=datetime(2026, 8, 25, 10, 0, 0),   # 5 days late
        area_affected_ha=Decimal("1.0"),
    )
    a = Assessment("CAL-Y", Decimal("40.0"), date(2026, 8, 26))
    enr = _enrolment(Decimal("1.0"), Decimal("52000"))
    assert localised_claim(n, a, enr, _nu01(), Decimal("0"), date(2026, 8, 26)) is None
