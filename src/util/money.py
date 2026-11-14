"""Money helpers. All amounts are Decimal; never float."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from src.config.constants import MONEY_QUANTUM

def D(value) -> Decimal:
    """Construct Decimal safely. Routes floats through str() first."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

def round_rupee(x: Decimal) -> Decimal:
    """Round to whole rupee, half-up (not banker's)."""
    return x.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)

def pct_of(amount: Decimal, pct: Decimal) -> Decimal:
    """`pct` percent of `amount`, rounded to rupee."""
    return round_rupee(amount * pct / Decimal("100"))

def rupee_str(x: Decimal) -> str:
    """For CSV: 2 dp, no comma, no symbol."""
    return f"{round_rupee(x):.2f}"
