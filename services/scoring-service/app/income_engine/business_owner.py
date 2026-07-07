from collections import defaultdict
from statistics import mean

from app.models.domain import Transaction

# Illustrative gross-margin bands by industry, not authoritative figures —
# a real deployment would source these from RBI/industry-body benchmarks or
# the bank's own portfolio data.
INDUSTRY_MARGIN_BANDS: dict[str, tuple[float, float]] = {
    "retail_trade": (0.08, 0.14),
    "professional_services": (0.20, 0.35),
    "manufacturing": (0.10, 0.18),
    "wholesale_trade": (0.05, 0.10),
}
DEFAULT_MARGIN_BAND = (0.08, 0.14)


def estimate_business_income(transactions: list[Transaction], industry: str | None = None) -> dict:
    """Turnover-times-industry-margin income path: sums UPI/bank credit
    turnover and applies a configurable margin band, reporting a
    low/mid/high confidence band rather than a single hard number — a
    business owner's income can't be pinned down as precisely as a salaried
    employee's from statement data alone, and presenting it as a single
    figure would overstate the certainty of the estimate.
    """
    income_txns = [t for t in transactions if t.category == "income"]
    if not income_txns:
        return {
            "monthly_turnover": 0.0,
            "monthly_income_estimate_low": 0.0,
            "monthly_income_estimate_mid": 0.0,
            "monthly_income_estimate_high": 0.0,
            "method": "turnover_margin",
            "sample_size": 0,
        }

    monthly_totals: dict[str, float] = defaultdict(float)
    for t in income_txns:
        monthly_totals[t.txn_date[:7]] += t.amount

    monthly_turnover = mean(monthly_totals.values())
    low_margin, high_margin = INDUSTRY_MARGIN_BANDS.get(industry, DEFAULT_MARGIN_BAND)
    mid_margin = (low_margin + high_margin) / 2

    return {
        "monthly_turnover": round(monthly_turnover, 2),
        "monthly_income_estimate_low": round(monthly_turnover * low_margin, 2),
        "monthly_income_estimate_mid": round(monthly_turnover * mid_margin, 2),
        "monthly_income_estimate_high": round(monthly_turnover * high_margin, 2),
        "method": "turnover_margin",
        "sample_size": len(monthly_totals),
    }
