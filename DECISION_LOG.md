# Decision Log — T009 / PS-097

| ID | Decision | Rationale |
|---|---|---|
| L1 | Offset (BR-10) uses approved net, not disbursed | Matches EC-08; disbursement may happen later |
| L2 | 100% cap applies to net after offset; reduces area-yield first | Actuarial solvency cap |
| L3 | Trigger-band strings: "20%","40%","60%","15%","15%+10%","25%","<loss_pct>%","N/A" | README requires exact output |
| L4 | BANK_ENROL after cut-off is REJECTED (same as ENROL) | Prevents adverse selection |
| L5 | Rejected enrolments excluded from premium CSV | "one row per accepted enrolment" |
| L6 | BR-04 10% haircut on final gross | Numerically identical; simpler |
| L7 | Missing day in deficit window contributes 0 mm | Deficit is a sum; missing = no credit |
| L8 | Missing-day count over whole 1 Jun – 30 Sep | README binding; EC-07 consistent |
| L9 | Third+ dry spell adds no further % (cap 25%) | Cap reached at 2 spells |
| L10 | Localised clock from unit FINALISE_YIELD for interest | Brief says "30 days of yield finalisation" |
| L11 | Same (farmer, survey) same unit twice rejected | No double insurance |
| L12 | Zero-payout claims emit no row | Cleaner claims.csv |
| L13 | PRINT_DISBURSEMENT_FILE includes payment_date ≤ as_of | Natural reading |
