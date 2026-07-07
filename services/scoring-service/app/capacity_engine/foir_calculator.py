from collections import defaultdict

from app.models.domain import Transaction

_EXPENSE_CATEGORIES = ("essential_needs", "compulsory_obligation", "discretionary", "savings_investment")


def compute_expense_summary(transactions: list[Transaction]) -> dict:
    """Average monthly spend per category, over however many months of
    statement history are present. Categories with no spend in a given month
    still count that month in the average (a month can genuinely have zero
    discretionary spend), since the denominator is the number of months
    observed at all, not the number of months a category happened to appear.
    """
    monthly: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for t in transactions:
        if t.direction != "debit" or t.category not in _EXPENSE_CATEGORIES:
            continue
        monthly[t.txn_date[:7]][t.category] += t.amount

    months = list(monthly.keys())
    n_months = len(months) or 1

    def avg(category: str) -> float:
        return round(sum(monthly[m].get(category, 0.0) for m in months) / n_months, 2)

    return {
        "essential_needs": avg("essential_needs"),
        "compulsory_obligations": avg("compulsory_obligation"),
        "discretionary_wants": avg("discretionary"),
        "savings_investment": avg("savings_investment"),
        "months_observed": len(months),
    }


def compute_disposable_income(monthly_income: float, expense_summary: dict) -> dict:
    """disposable_income excludes discretionary/savings deliberately: those
    are choices the customer could redirect toward a new EMI, whereas
    essential needs and existing compulsory obligations cannot be.
    """
    disposable_income = monthly_income - expense_summary["essential_needs"] - expense_summary["compulsory_obligations"]
    foir_pct = (expense_summary["compulsory_obligations"] / monthly_income) if monthly_income > 0 else 0.0

    return {
        "disposable_income": round(disposable_income, 2),
        "foir_pct": round(foir_pct, 4),
    }
