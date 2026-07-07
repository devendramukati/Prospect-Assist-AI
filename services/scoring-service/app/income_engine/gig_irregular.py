from collections import defaultdict
from statistics import mean, pstdev

from app.models.domain import Transaction


def estimate_gig_income(transactions: list[Transaction]) -> dict:
    """Irregular/multi-source income path: a recency-weighted average of
    monthly credit totals, discounted by volatility — a gig worker's most
    recent months matter more than older ones, and a highly volatile
    earner's income should be estimated conservatively rather than at face
    value.
    """
    income_txns = [t for t in transactions if t.category == "income"]
    if not income_txns:
        return {"monthly_income_estimate": 0.0, "income_stability_score": 0.0, "method": "rolling_avg", "sample_size": 0}

    monthly_totals: dict[str, float] = defaultdict(float)
    for t in income_txns:
        monthly_totals[t.txn_date[:7]] += t.amount

    months_sorted = sorted(monthly_totals.keys())
    totals = [monthly_totals[m] for m in months_sorted]

    weights = list(range(1, len(totals) + 1))  # most recent month gets the highest weight
    weighted_mean = sum(t * w for t, w in zip(totals, weights)) / sum(weights)

    avg = mean(totals)
    cov = (pstdev(totals) / avg) if avg > 0 else 1.0
    volatility_discount = max(0.0, 1 - min(cov, 1.0))

    return {
        "monthly_income_estimate": round(weighted_mean * volatility_discount, 2),
        "income_stability_score": round(max(0.0, min(1.0, 1 - cov)), 2),
        "method": "rolling_avg",
        "sample_size": len(months_sorted),
    }
