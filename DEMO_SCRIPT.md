# 5-Minute Demo Script — PS-097

## [0:00-0:30] Project intro

"PS-097 is a command-driven crop insurance engine in Python 3.10+.
Reads 10 master CSVs and a commands file, applies 12 business rules,
produces 3 output CSVs: premiums, claims, disbursements.
Modular monolith: one module per rule, pure functions, 69 pytest cases."

Show: ls src/rules/ — 12 files

## [0:30-1:00] Running the engine

python run.py data output
wc -l output/*.csv

"Processed 248 commands -> 147 enrolments, 447 claims, 353 disbursement rows."

## [1:00-1:45] Premium calculation (BR-01)

"FMR-0043, NU-02, 1.30 ha, SI/ha = 38,000:
- SI = 49,400
- Total premium = 5,187
- Farmer 2% = 988
- Subsidy 2,100 + 2,099"

Show: head -2 output/premium_statement.csv

## [1:45-2:30] Weather + offset (BR-06 + BR-10, EC-03 + EC-08)

"FMR-0003 NU-01: 22-day dry spell, 2.5mm day, 22-day dry spell -> 15%+10% = 25% SI = 17,160.
Area-yield would be 10,764 but weather already paid 17,160 -> BR-10 offsets to 0. No double indemnity."

Show: grep "FMR-0003" output/claims.csv

## [2:30-3:15] Prevented sowing after weather (EC-05)

"NU-06 gets 40% deficit rain paid 8 Aug.
15 Aug sowing = 858 < 975 threshold -> prevented sowing 25% SI, unit TERMINATED.
No dry spell, no excess, no area-yield after. Prior weather stands."

Show: grep "^NU-06" output/claims.csv

## [3:15-4:00] Disbursement + interest (BR-11)

"NU-01: 20 Oct -> 19 Nov = 30 days exactly, no interest.
NU-02: 20 Oct -> 4 Dec = 45 days -> 15 days × 12% p.a.
FMR-0030 INACTIVE bank -> HELD, 0 interest."

Show: grep "FMR-0030" output/disbursement.csv

## [4:00-4:30] Tests

python -m pytest tests/ -v

"69 tests: 4-7 per BR + smoke. All 8 edge cases verified."

## [4:30-5:00] Design decisions

"See DECISION_LOG.md — L1-L13."

## Q&A prep

Q: Why one module per rule?
A: Testability + reviewer readability.

Q: How do you prevent double indemnity?
A: BR-10 apply_caps — offset_reduction = prior weather+localised net; cap_reduction = overflow past 100% SI.

Q: Why Decimal not float?
A: Float error: 0.1+0.2=0.30000000000000004. Decimal is exact to the rupee.

Q: Missing station days?
A: BR-07 — >10 missing -> nearest <=25km; else NOT_ASSESSABLE.
