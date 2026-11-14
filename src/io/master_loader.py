"""Load all 8 master CSVs into typed objects. Fails fast on bad data."""
from __future__ import annotations
from pathlib import Path
from decimal import Decimal

from src.config.enums import AccountStatus, CropCategory, RiskLevel
from src.domain.models import (
    CCEYield, Farmer, LandRecord, NotifiedUnit, SowingReport, Station, YieldHistory,
)
from src.io.csv_loader import MasterDataError, read_csv
from src.repository.master_repo import MasterRepo
from src.repository.weather_repo import WeatherRepo


def _d(v: str) -> Decimal:
    return Decimal(v)


def load_stations(data_dir: Path) -> dict[str, Station]:
    out: dict[str, Station] = {}
    for r in read_csv(data_dir / "stations.csv"):
        s = Station(r["station_id"], r["station_name"], r["district"])
        if s.station_id in out:
            raise MasterDataError(f"duplicate station {s.station_id}")
        out[s.station_id] = s
    return out


def load_station_distances(data_dir: Path) -> dict[tuple[str, str], Decimal]:
    out: dict[tuple[str, str], Decimal] = {}
    for r in read_csv(data_dir / "station_distances.csv"):
        a, b = r["station_a"], r["station_b"]
        key = (a, b) if a < b else (b, a)
        out[key] = _d(r["distance_km"])
    return out


def load_notified_units(data_dir: Path) -> dict[str, NotifiedUnit]:
    out: dict[str, NotifiedUnit] = {}
    for r in read_csv(data_dir / "notified_units.csv"):
        u = NotifiedUnit(
            unit_id=r["unit_id"], district=r["district"], block=r["block"],
            crop=r["crop"], crop_category=CropCategory(r["crop_category"]),
            season=r["season"], risk_level=RiskLevel(r["risk_level"]),
            indemnity_level_pct=int(r["indemnity_level_pct"]),
            sum_insured_per_ha=_d(r["sum_insured_per_ha"]),
            actuarial_rate_pct=_d(r["actuarial_rate_pct"]),
            normal_area_ha=_d(r["normal_area_ha"]),
            station_id=r["station_id"],
            normal_rain_jun_jul_mm=_d(r["normal_rain_jun_jul_mm"]),
            block_yield_kg_ha=int(r["block_yield_kg_ha"]),
        )
        if u.unit_id in out:
            raise MasterDataError(f"duplicate unit {u.unit_id}")
        out[u.unit_id] = u
    return out


def load_farmers(data_dir: Path) -> dict[str, Farmer]:
    out: dict[str, Farmer] = {}
    for r in read_csv(data_dir / "farmers.csv"):
        f = Farmer(
            farmer_id=r["farmer_id"], farmer_name=r["farmer_name"],
            gender=r["gender"], village=r["village"], mobile=r["mobile"],
            bank_account=r["bank_account"], ifsc=r["ifsc"],
            account_status=AccountStatus(r["account_status"]),
        )
        if f.farmer_id in out:
            raise MasterDataError(f"duplicate farmer {f.farmer_id}")
        out[f.farmer_id] = f
    return out


def load_land_records(data_dir: Path) -> dict[str, LandRecord]:
    out: dict[str, LandRecord] = {}
    for r in read_csv(data_dir / "land_records.csv"):
        lr = LandRecord(
            survey_no=r["survey_no"], farmer_id=r["farmer_id"],
            village=r["village"], unit_id=r["unit_id"], area_ha=_d(r["area_ha"]),
        )
        if lr.survey_no in out:
            raise MasterDataError(f"duplicate survey {lr.survey_no}")
        out[lr.survey_no] = lr
    return out


def load_yield_history(data_dir: Path) -> dict[str, list[YieldHistory]]:
    out: dict[str, list[YieldHistory]] = {}
    for r in read_csv(data_dir / "yield_history.csv"):
        y = YieldHistory(r["unit_id"], int(r["year"]), int(r["yield_kg_ha"]))
        out.setdefault(y.unit_id, []).append(y)
    return out


def load_cce_yields(data_dir: Path) -> dict[str, list[CCEYield]]:
    from src.util.dates import parse_date
    out: dict[str, list[CCEYield]] = {}
    for r in read_csv(data_dir / "cce_yields.csv"):
        c = CCEYield(
            cce_id=r["cce_id"], unit_id=r["unit_id"], survey_no=r["survey_no"],
            experiment_date=parse_date(r["experiment_date"]),
            yield_kg_ha=int(r["yield_kg_ha"]),
        )
        out.setdefault(c.unit_id, []).append(c)
    return out


def load_sowing_reports(data_dir: Path) -> dict[str, list[SowingReport]]:
    from src.util.dates import parse_date
    out: dict[str, list[SowingReport]] = {}
    for r in read_csv(data_dir / "sowing_reports.csv"):
        s = SowingReport(
            report_id=r["report_id"], unit_id=r["unit_id"],
            report_date=parse_date(r["report_date"]),
            area_sown_ha=_d(r["area_sown_ha"]),
        )
        out.setdefault(s.unit_id, []).append(s)
    return out


def load_weather(data_dir: Path) -> WeatherRepo:
    from src.util.dates import parse_date
    rain: dict[str, dict] = {}
    for r in read_csv(data_dir / "weather_daily.csv"):
        station = r["station_id"]
        d = parse_date(r["obs_date"])
        rain.setdefault(station, {})[d] = _d(r["rainfall_mm"])
    return WeatherRepo(rain)


def load_masters(data_dir: Path) -> MasterRepo:
    """Load all master CSVs, cross-validate, return MasterRepo."""
    stations = load_stations(data_dir)
    distances = load_station_distances(data_dir)
    units = load_notified_units(data_dir)
    farmers = load_farmers(data_dir)
    land = load_land_records(data_dir)
    yields = load_yield_history(data_dir)
    cces = load_cce_yields(data_dir)
    sowing = load_sowing_reports(data_dir)

    # Cross-validate
    for u in units.values():
        if u.station_id not in stations:
            raise MasterDataError(f"unit {u.unit_id} references unknown station {u.station_id}")
        if u.unit_id not in yields:
            raise MasterDataError(f"unit {u.unit_id} has no yield history")
    for lr in land.values():
        if lr.unit_id not in units:
            raise MasterDataError(f"land {lr.survey_no} references unknown unit {lr.unit_id}")
        if lr.farmer_id not in farmers:
            raise MasterDataError(f"land {lr.survey_no} references unknown farmer {lr.farmer_id}")

    return MasterRepo(
        stations=stations, distances=distances, units=units, farmers=farmers,
        land=land, yields=yields, cces=cces, sowing=sowing,
    )
