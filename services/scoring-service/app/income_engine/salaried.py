from statistics import mean, pstdev

from app.models.domain import Transaction

# Empirically, a well-behaved salary has ~1-3% month-to-month variance
# (rounding, small bonuses); this scale factor maps that to a 0.85-0.95
# stability score, while variance above ~20% (job change, missed month)
# drops the score toward 0.
_STABILITY_SCALE = 5.0


def estimate_salaried_income(transactions: list[Transaction]) -> dict:
    """Fixed-salary income path: a recurring monthly credit with low
    month-to-month variance. Prefers transactions the recurring-transaction
    detector (Phase 2) already flagged; falls back to the salary subcategory
    alone if recurrence wasn't detected (e.g. too few months observed).
    """
    salary_txns = [t for t in transactions if t.category == "income" and t.is_recurring]
    if not salary_txns:
        salary_txns = [t for t in transactions if t.category == "income" and t.subcategory == "salary"]

    if not salary_txns:
        return {"monthly_income_estimate": 0.0, "income_stability_score": 0.0, "method": "fixed_salary", "sample_size": 0}

    amounts = sorted(t.amount for t in salary_txns)
    mid = len(amounts) // 2
    median_amount = amounts[mid] if len(amounts) % 2 == 1 else (amounts[mid - 1] + amounts[mid]) / 2

    avg = mean(amounts)
    cov = (pstdev(amounts) / avg) if avg > 0 else 1.0
    stability_score = max(0.0, min(1.0, 1 - cov * _STABILITY_SCALE))

    return {
        "monthly_income_estimate": round(median_amount, 2),
        "income_stability_score": round(stability_score, 2),
        "method": "fixed_salary",
        "sample_size": len(salary_txns),
    }
