from collections import defaultdict
from datetime import date
from statistics import mean

from app.models.domain import Transaction

# A credit only counts as a "payday" event if it's individually a meaningful
# share of that month's total income — otherwise a turnover-style account
# with many small, similarly-sized UPI credits (a business owner) would have
# no single dominant credit, and comparing a large lump-sum debit (e.g. an
# EMI) against one arbitrary small credit produces a meaningless >100% ratio.
SIGNIFICANT_CREDIT_SHARE = 0.15


def compute_day1_spend_velocity(transactions: list[Transaction]) -> dict:
    """% of each month's dominant income credit(s) that leaves the account
    within 0-2 days — the concrete signal for a "spends the salary
    immediately" delinquency-risk pattern, independent of category labels
    (it looks at all debits in the window, not just discretionary ones,
    since a big EMI/rent payment scheduled right after salary day would be
    a legitimate reason for the same pattern and still worth surfacing).

    Months with no individually-significant credit (e.g. a business account
    funded by many small, similarly-sized UPI credits) are excluded rather
    than measured against an arbitrary small credit.
    """
    by_month: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        by_month[t.txn_date[:7]].append(t)

    monthly_ratios = []
    for month_txns in by_month.values():
        all_credits = [t for t in month_txns if t.direction == "credit"]
        total_month_income = sum(t.amount for t in all_credits)
        if total_month_income == 0:
            continue

        significance_floor = SIGNIFICANT_CREDIT_SHARE * total_month_income
        significant_credits = sorted(
            (t for t in all_credits if t.amount >= significance_floor), key=lambda t: t.amount, reverse=True
        )[:3]
        if not significant_credits:
            continue

        total_credit = sum(t.amount for t in significant_credits)
        credit_dates = [date.fromisoformat(c.txn_date) for c in significant_credits]
        day1_total = sum(
            t.amount
            for t in month_txns
            if t.direction == "debit"
            and any(0 <= (date.fromisoformat(t.txn_date) - cd).days <= 2 for cd in credit_dates)
        )
        monthly_ratios.append(day1_total / total_credit)

    if not monthly_ratios:
        return {"day1_spend_velocity_pct": 0.0, "months_observed": 0}

    return {
        "day1_spend_velocity_pct": round(mean(monthly_ratios), 4),
        "months_observed": len(monthly_ratios),
    }
