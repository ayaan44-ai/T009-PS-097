"""Handlers — one function per command verb.

Each handler: reads state, calls pure rules, mutates state.
No file IO. No rule logic (rules live in src/rules/).
"""
from __future__ import annotations
import logging
from datetime import date
from decimal import Decimal

from src.config.constants import ENROLMENT_CUTOFF, OPT_OUT_CUTOFF, SOWING_REPORT_EVAL_DATE
from src.config.enums import (
    ClaimStatus, ClaimType, EnrolmentStatus, TriggerType, UnitStatus,
)
from src.domain.models import Enrolment, CalamityNotification, Assessment, Claim
from src.engine.commands import (
    AssessCommand, BankEnrolCommand, CalamityCommand, DisburseCommand,
    EnrolCommand, EvalSowingCommand, EvalWeatherCommand, FinaliseYieldCommand,
    OptOutCommand, PrintClaimsCommand, PrintDisbursementCommand, PrintPremiumCommand,
)
from src.engine.state import EngineState
from src.rules import br01_premium, br02_enrolment, br03_threshold, br04_area_yield
from src.rules import br05_deficit, br06_dry_spell, br07_excess_rain
from src.rules import br08_prevented, br09_localised, br10_caps, br11_disbursement
from src.util.money import D, round_rupee

log = logging.getLogger("handlers")


def handle_enrol(cmd: EnrolCommand, state: EngineState) -> None:
    """Non-loanee enrolment. Rejected if after cut-off or invalid area."""
    m = state.masters
    if cmd.unit_id not in m.units or cmd.farmer_id not in m.farmers or cmd.survey_no not in m.land:
        log.warning("enrol %s rejected: unknown IDs", cmd.enrolment_id)
        return
    land = m.land[cmd.survey_no]
    unit = m.units[cmd.unit_id]

    if land.farmer_id != cmd.farmer_id or land.unit_id != cmd.unit_id:
        log.warning("enrol %s rejected: land/farmer/unit mismatch", cmd.enrolment_id)
        return

    v = br02_enrolment.validate_enrolment_date(cmd.file_date)
    if not v.ok:
        log.warning("enrol %s rejected: %s", cmd.enrolment_id, v.reason)
        _register_rejected_enrolment(cmd, state, EnrolmentStatus.REJECTED)
        return

    if br12_dup_check(cmd, state):
        log.warning("enrol %s rejected: duplicate survey", cmd.enrolment_id)
        _register_rejected_enrolment(cmd, state, EnrolmentStatus.REJECTED)
        return

    av = br02_enrolment.validate_area(cmd.area_sown_ha, land)
    if not av.ok:
        log.warning("enrol %s rejected: %s", cmd.enrolment_id, av.reason)
        _register_rejected_enrolment(cmd, state, EnrolmentStatus.REJECTED)
        return

    _accept_enrolment(cmd, state, unit)


def handle_bank_enrol(cmd: BankEnrolCommand, state: EngineState) -> None:
    """Loanee auto-enrolment. Same validations as ENROL (locked decision L4)."""
    handle_enrol(cmd, state)


def handle_opt_out(cmd: OptOutCommand, state: EngineState) -> None:
    v = br02_enrolment.validate_opt_out_date(cmd.request_date)
    if not v.ok:
        log.warning("opt-out %s/%s rejected: %s", cmd.farmer_id, cmd.unit_id, v.reason)
        return
    # Find active enrolment for this farmer in this unit
    for e in state.enrolments.accepted:
        if e.farmer_id == cmd.farmer_id and e.unit_id == cmd.unit_id:
            e.status = EnrolmentStatus.OPTED_OUT
            log.info("opt-out %s/%s applied", cmd.farmer_id, cmd.unit_id)
            return
    log.warning("opt-out %s/%s: no active enrolment", cmd.farmer_id, cmd.unit_id)


def br12_dup_check(cmd: EnrolCommand, state: EngineState) -> bool:
    from src.rules.br12_validation import find_duplicate_survey
    active = [e for e in state.enrolments.accepted if e.status == EnrolmentStatus.ACTIVE]
    return find_duplicate_survey(active, cmd.farmer_id, cmd.survey_no) is not None


def _register_rejected_enrolment(cmd: EnrolCommand, state: EngineState, status: EnrolmentStatus) -> None:
    state.enrolments.add_rejected(Enrolment(
        enrolment_id=cmd.enrolment_id, farmer_id=cmd.farmer_id, unit_id=cmd.unit_id,
        survey_no=cmd.survey_no, area_insured_ha=D("0"), sum_insured=D("0"),
        total_premium=D("0"), farmer_premium=D("0"), state_subsidy=D("0"),
        centre_subsidy=D("0"), status=status, created_date=cmd.file_date,
    ))


def _accept_enrolment(cmd: EnrolCommand, state: EngineState, unit) -> None:
    pb = br01_premium.compute_premium(unit, cmd.area_sown_ha)
    e = Enrolment(
        enrolment_id=cmd.enrolment_id, farmer_id=cmd.farmer_id, unit_id=cmd.unit_id,
        survey_no=cmd.survey_no, area_insured_ha=cmd.area_sown_ha,
        sum_insured=pb.sum_insured, total_premium=pb.total_premium,
        farmer_premium=pb.farmer_premium, state_subsidy=pb.state_subsidy,
        centre_subsidy=pb.centre_subsidy, status=EnrolmentStatus.ACTIVE,
        created_date=cmd.file_date,
    )
    state.enrolments.add_accepted(e)
    log.info("enrol %s accepted: %s ha, SI=%s", cmd.enrolment_id, cmd.area_sown_ha, pb.sum_insured)


# =============================================================================
# Weather handlers
# =============================================================================
def handle_eval_weather(cmd: EvalWeatherCommand, state: EngineState) -> None:
    if state.is_unit_terminated(cmd.unit_id):
        log.info("weather %s/%s skipped: unit terminated", cmd.unit_id, cmd.trigger)
        return
    m = state.masters
    if cmd.unit_id not in m.units:
        return
    unit = m.units[cmd.unit_id]

    # Determine effective station (BR-07 replacement)
    distances = m.distances
    missing_count = state.weather.missing_count(unit.station_id)
    eff_station = br07_excess_rain.effective_station(unit.station_id, missing_count, distances)
    if eff_station is None:
        log.warning("weather %s: no station assessable", cmd.unit_id)
        return

    trigger = cmd.trigger
    if trigger == TriggerType.DEFICIT_RAIN.value:
        rain_sum = state.weather.sum_rain_between(
            eff_station,
            __import__("src.config.constants", fromlist=["DEFICIT_WINDOW_START"]).DEFICIT_WINDOW_START,
            __import__("src.config.constants", fromlist=["DEFICIT_WINDOW_END"]).DEFICIT_WINDOW_END,
        )
        pct, band = br05_deficit.deficit_band(rain_sum, unit.normal_rain_jun_jul_mm)
    elif trigger == TriggerType.DRY_SPELL.value:
        from src.config.constants import DRY_EXCESS_WINDOW_START, DRY_EXCESS_WINDOW_END
        series = state.weather.rain_series(eff_station)
        result = br06_dry_spell.dry_spell(series, DRY_EXCESS_WINDOW_START, DRY_EXCESS_WINDOW_END)
        pct, band = result.pct, result.band_str
    elif trigger == TriggerType.EXCESS_RAIN.value:
        from src.config.constants import DRY_EXCESS_WINDOW_START, DRY_EXCESS_WINDOW_END
        series = state.weather.rain_series(eff_station)
        qualifies, band = br07_excess_rain.excess_rain_qualifies(
            series, DRY_EXCESS_WINDOW_START, DRY_EXCESS_WINDOW_END)
        from src.config.constants import EXCESS_PAYOUT_PCT
        pct = EXCESS_PAYOUT_PCT if qualifies else Decimal("0")
    else:
        log.warning("unknown trigger %s", trigger)
        return

    if pct <= Decimal("0"):
        log.info("weather %s/%s: no payout (band=%s)", cmd.unit_id, trigger, band)
        return

    claim_type = {
        TriggerType.DEFICIT_RAIN.value: ClaimType.DEFICIT_RAIN,
        TriggerType.DRY_SPELL.value: ClaimType.DRY_SPELL,
        TriggerType.EXCESS_RAIN.value: ClaimType.EXCESS_RAIN,
    }[trigger]

    for enr in state.enrolments.active_for_unit(cmd.unit_id):
        if enr.status != EnrolmentStatus.ACTIVE:
            continue
        gross = round_rupee(enr.sum_insured * pct / Decimal("100"))
        if gross <= Decimal("0"):
            continue
        prior = state.claims_for_farmer_unit(cmd.unit_id, enr.farmer_id)
        raw = Claim(
            unit_id=cmd.unit_id, farmer_id=enr.farmer_id, claim_type=claim_type,
            trigger_band=band, gross_amount=gross, status=ClaimStatus.PENDING,
            rule_id=f"BR-0{5 + ['DEFICIT_RAIN','DRY_SPELL','EXCESS_RAIN'].index(trigger)}",
            finalisation_date=cmd.eval_date, created_date=cmd.eval_date,
        )
        capped = br10_caps.apply_caps(raw, enr, prior)
        state.add_claim(capped)


# =============================================================================
# Sowing handler (BR-08)
# =============================================================================
def handle_eval_sowing(cmd: EvalSowingCommand, state: EngineState) -> None:
    if state.is_unit_terminated(cmd.unit_id):
        return
    m = state.masters
    if cmd.unit_id not in m.units:
        return
    unit = m.units[cmd.unit_id]
    reports = [r for r in m.sowing_for(cmd.unit_id) if r.report_date == SOWING_REPORT_EVAL_DATE]
    if not reports:
        log.warning("sowing %s: no 15 Aug report", cmd.unit_id)
        return
    report = reports[0]
    if not br08_prevented.is_prevented(report, unit):
        log.info("sowing %s: not prevented (sown=%s, threshold=%s)",
                 cmd.unit_id, report.area_sown_ha, unit.normal_area_ha * Decimal("0.25"))
        return
    for enr in state.enrolments.active_for_unit(cmd.unit_id):
        if enr.status != EnrolmentStatus.ACTIVE:
            continue
        claim = br08_prevented.prevented_claim(enr, unit, cmd.eval_date)
        prior = state.claims_for_farmer_unit(cmd.unit_id, enr.farmer_id)
        capped = br10_caps.apply_caps(claim, enr, prior)
        state.add_claim(capped)
    state.terminate_unit(cmd.unit_id)
    log.info("sowing %s: PREVENTED SOWING, unit terminated", cmd.unit_id)


# =============================================================================
# Calamity handlers (BR-09)
# =============================================================================
def handle_calamity(cmd: CalamityCommand, state: EngineState) -> None:
    from src.domain.models import CalamityNotification
    notif = CalamityNotification(
        notification_id=cmd.notification_id, farmer_id=cmd.farmer_id,
        unit_id=cmd.unit_id, event_type=cmd.event_type,
        event_ts=cmd.event_ts, notify_ts=cmd.notify_ts,
        area_affected_ha=cmd.area_affected_ha,
    )
    if not br09_localised.is_notification_on_time(notif):
        state.rejected_notifications.add(cmd.notification_id)
        log.warning("calamity %s rejected: late notification", cmd.notification_id)
        return
    state.notifications[cmd.notification_id] = notif


def handle_assess(cmd: AssessCommand, state: EngineState) -> None:
    from src.domain.models import Assessment
    if cmd.notification_id in state.rejected_notifications:
        return
    if cmd.notification_id not in state.notifications:
        log.warning("assess %s: no notification", cmd.notification_id)
        return
    notif = state.notifications[cmd.notification_id]
    assessment = Assessment(
        notification_id=cmd.notification_id,
        loss_pct=cmd.loss_pct,
        assess_date=cmd.assess_date,
    )
    state.assessments[cmd.notification_id] = assessment

    m = state.masters
    if notif.unit_id not in m.units or notif.farmer_id not in m.farmers:
        return
    unit = m.units[notif.unit_id]
    enr = None
    for e in state.enrolments.active_for_unit(notif.unit_id):
        if e.farmer_id == notif.farmer_id and e.status == EnrolmentStatus.ACTIVE:
            enr = e
            break
    if enr is None:
        return
    weather_paid = state.net_weather_paid_for_farmer(notif.unit_id, notif.farmer_id)
    claim = br09_localised.localised_claim(
        notif, assessment, enr, unit, weather_paid, cmd.assess_date,
    )
    if claim is None:
        return
    prior = state.claims_for_farmer_unit(notif.unit_id, notif.farmer_id)
    capped = br10_caps.apply_caps(claim, enr, prior)
    state.add_claim(capped)


# =============================================================================
# Yield handler (BR-03, BR-04) — FINALISE_YIELD
# =============================================================================
def handle_finalise_yield(cmd: FinaliseYieldCommand, state: EngineState) -> None:
    if state.is_unit_terminated(cmd.unit_id):
        log.info("finalise %s skipped: unit terminated", cmd.unit_id)
        return
    m = state.masters
    if cmd.unit_id not in m.units:
        return
    unit = m.units[cmd.unit_id]
    history = m.yields_for(cmd.unit_id)
    cces = m.cces_for(cmd.unit_id)

    threshold = br03_threshold.threshold_yield(unit, history)

    for enr in state.enrolments.active_for_unit(cmd.unit_id):
        if enr.status != EnrolmentStatus.ACTIVE:
            continue
        claim = br04_area_yield.area_yield_claim(enr, unit, threshold, cces, cmd.finalise_date)
        if claim is None:
            continue
        prior = state.claims_for_farmer_unit(cmd.unit_id, enr.farmer_id)
        capped = br10_caps.apply_caps(claim, enr, prior)
        state.add_claim(capped)

    state.unit_finalise_date[cmd.unit_id] = cmd.finalise_date
    log.info("finalise %s: threshold=%s, %d enrolments processed",
             cmd.unit_id, threshold, len(state.enrolments.active_for_unit(cmd.unit_id)))


# =============================================================================
# Disburse handler (BR-11)
# =============================================================================
def handle_disburse(cmd: DisburseCommand, state: EngineState) -> None:
    claims = state.all_claims_for_unit(cmd.unit_id)
    finalise_date = state.unit_finalise_date.get(cmd.unit_id)
    rows = br11_disbursement.disbursement_rows_for_unit(
        unit_id=cmd.unit_id,
        payment_date=cmd.payment_date,
        claims=claims,
        farmers=state.masters.farmers,
        already_paid_keys=state.paid_claim_keys,
        unit_finalise_date=finalise_date,
    )
    for r in rows:
        state.disbursements.append(r)
        state.paid_claim_keys.add((r.unit_id, r.farmer_id, r.claim_type.value))
    log.info("disburse %s @ %s: %d rows", cmd.unit_id, cmd.payment_date, len(rows))


# =============================================================================
# Print handlers — queue rows for writers
# =============================================================================
def handle_print_premium(cmd: PrintPremiumCommand, state: EngineState, buffer: dict) -> None:
    buffer.setdefault("premium", [])
    for enr in state.enrolments.accepted:
        if enr.unit_id == cmd.unit_id:
            buffer["premium"].append(enr)


def handle_print_claims(cmd: PrintClaimsCommand, state: EngineState, buffer: dict) -> None:
    buffer.setdefault("claims", [])
    for claim in state.all_claims_for_unit(cmd.unit_id):
        buffer["claims"].append(claim)


def handle_print_disbursement(cmd: PrintDisbursementCommand, state: EngineState, buffer: dict) -> None:
    buffer.setdefault("disbursement", [])
    for r in state.disbursements:
        if r.payment_date <= cmd.as_of_date:
            buffer["disbursement"].append(r)
