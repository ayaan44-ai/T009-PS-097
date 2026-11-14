# PS-097 — Design Document

Team: T009 · Language: Python 3.10+ · Architecture: Modular monolith, command-driven, no UI

## 1. Architecture

INPUT LAYER (read once): 10 master CSVs
       |
       v
DATA LAYER: MasterRepo, WeatherRepo, EnrolmentRepo
       |
       v
ENGINE LAYER: Processor -> Handlers -> RuleService -> EngineState
       |
       v
OUTPUT LAYER: PremiumWriter, ClaimsWriter, DisbursementWriter

Principles:
1. Single source of truth — all mutable state in EngineState
2. Separation of concerns — loaders parse, rules compute, writers format
3. Pure rules — each BR is a pure function (easy to test)
4. Immutable masters — after load, master data is read-only
5. Fail loud — master data issues raise at startup

## 2. Folder Structure

src/config/       constants.py, enums.py
src/domain/       models.py (14 dataclasses)
src/io/           csv_loader, master_loader, command_parser, writers
src/repository/   master_repo, weather_repo, enrolment_repo
src/rules/        br01..br12 (one module per rule)
src/engine/       state, commands, handlers, processor
src/util/         money, dates, logging
tests/            12 BR test files + smoke
run.py            CLI entry point

## 3. Class Diagram (simplified)

EngineState
  - MasterRepo (stations, units, farmers, land, yields, cces, sowing)
  - WeatherRepo (rainfall, missing days)
  - EnrolmentRepo (accepted, rejected)
  - claims: dict[(unit, farmer), list[Claim]]
  - disbursements: list[Disbursement]
  - unit_status: dict[unit, ACTIVE|TERMINATED]

Processor
  - EngineState
  - Command -> Handler -> Rule -> State mutation

RuleService (12 pure functions):
  br01_premium.compute_premium
  br02_enrolment.validate_*
  br03_threshold.threshold_yield
  br04_area_yield.area_yield_claim
  br05_deficit.deficit_band
  br06_dry_spell.dry_spell
  br07_excess_rain.excess_rain_qualifies, effective_station
  br08_prevented.is_prevented, prevented_claim
  br09_localised.is_notification_on_time, localised_claim
  br10_caps.apply_caps
  br11_disbursement.delay_days_for, interest_for, disbursement_rows_for_unit
  br12_validation.find_duplicate_survey, cap_area

## 4. State Diagram — Enrolment Lifecycle

[*] -> Received (ENROL/BANK_ENROL)
Received -> Rejected (BR-02, BR-12, L4)
Received -> Active (valid, BR-01 premium)
Active -> OptedOut (OPT_OUT <= 24 Jul)
Active -> Terminated (BR-08 prevented sowing, 25% SI paid)
Active -> Claimed (weather/localised/area-yield)
Claimed -> Settled (DISBURSE pays net+interest)
Claimed -> Held (farmer INACTIVE, no interest)
Terminated -> Settled (DISBURSE pays prevented-sowing)

## 5. Business Rule Register

BR-01 Premium = SI × rate; farmer 2%/5%; subsidy split | br01_premium | 4 tests
BR-02 Cut-off 31 Jul; OPT_OUT <= 24 Jul; area <= land | br02_enrolment | 5 tests
BR-03 Threshold = avg(best 5 of 7) × 90/80/70% | br03_threshold | 5 tests
BR-04 Area-yield; >=4 CCE mean else block+10% haircut | br04_area_yield | 5 tests
BR-05 Deficit <75/60/40% -> 20/40/60% SI | br05_deficit | 6 tests
BR-06 Dry spell >=20d <2.5mm -> 15%+10% cap 25% | br06_dry_spell | 6 tests
BR-07 Excess 3-day >200mm -> 15%; >10 missing -> replace | br07_excess_rain | 7 tests
BR-08 Prevented <25% by 15 Aug -> 25% SI, terminate | br08_prevented | 5 tests
BR-09 Localised <=72h; loss% × SI × area; 50% cap | br09_localised | 5 tests
BR-10 Total <=100% SI; area-yield offset | br10_caps | 5 tests
BR-11 Pay <=30d; delay 12% p.a.; INACTIVE -> HELD | br11_disbursement | 7 tests
BR-12 Duplicate survey rejected; area cap | br12_validation | 7 tests

## 6. Error Handling

Master load: fail fast (MasterDataError), exit 1
Command parse: log warning, skip line
Rule exception: log error, skip command
Business rejection: create Enrolment(status=REJECTED), no premium row

## 7. Test Coverage

69 tests across 13 files. All 12 BRs covered. All 8 ECs verified in production.

## 8. Locked Decisions

See DECISION_LOG.md for L1-L13.
