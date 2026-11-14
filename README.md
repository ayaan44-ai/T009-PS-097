# T009 — PS-097 · Crop Insurance Claim Engine

Command-file-driven back-end for a crop insurer. Reads 10 master CSVs plus
`commands.txt`, computes premiums and claims under 12 business rules, and
writes three output CSVs. No UI. Python 3.10+, standard library only.

**Team:** T009 — Ayaan Asif Vijaliwadha (1AT24CD018), Bhoomika H A (1AT24CD019)

## Quick start

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py data output
python -m pytest tests/ -v

## Output

Three CSVs written to output/:
- premium_statement.csv — one row per accepted enrolment
- claims.csv — one row per farmer per unit per claim type
- disbursement.csv — one row per payment line

## Business rules

BR-01 Premium = SI × rate; farmer 2% (Kharif food) / 5% (commercial); subsidy split equally
BR-02 Kharif cut-off 31 Jul; OPT_OUT ≤ 24 Jul; area ≤ land record
BR-03 Threshold = avg(best 5 of 7 yrs) × 90/80/70%
BR-04 Area-yield shortfall; <4 CCE → block yield with 10% haircut
BR-05 Deficit rain <75/60/40% → 20/40/60% SI
BR-06 Dry spell ≥20 days <2.5 mm → 15%; second +10%; cap 25%
BR-07 Excess rain 3-day >200 mm → 15%; station replaced if >10 missing
BR-08 Prevented sowing <25% by 15 Aug → 25% SI, terminate
BR-09 Localised calamity ≤72 h; loss% × SI × area; 50% cap with weather
BR-10 Total ≤100% SI; area-yield offset by weather + localised
BR-11 Pay ≤30 days; delay → 12% p.a.; INACTIVE → HELD
BR-12 Duplicate survey → REJECTED; claim area capped at enrolled

## Edge cases (all verified in production)

EC-01 75% cumulative rain exact → no payout
EC-02 20 dry days ending 30 Sep → 15% SI
EC-03 two spells separated by exactly 2.5 mm → 25% SI
EC-04 exactly 4 CCEs → mean used, no haircut
EC-05 prevented sowing after weather paid → prior payment stands
EC-06 localised notification at 72 h exactly → accepted
EC-07 exactly 10 missing days → station stays assessable
EC-08 area-yield fully offset by weather → net = 0

## Project layout

src/config/       constants + enums
src/domain/       dataclasses
src/io/           CSV loaders, command parser, writers
src/repository/   in-memory queryable state
src/rules/        one module per business rule (pure functions)
src/engine/       command dispatch, state, handlers
src/util/         money, dates, logging
tests/            pytest suite (69 tests)

See DESIGN.md for architecture and DECISION_LOG.md for locked assumptions.
