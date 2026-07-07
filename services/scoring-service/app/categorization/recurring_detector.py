from collections import defaultdict
from datetime import date

from app.models.domain import Transaction


def detect_recurring(
    transactions: list[Transaction],
    min_occurrences: int = 3,
    amount_tolerance_pct: float = 0.25,
    day_tolerance: int = 5,
) -> list[Transaction]:
    """Flags a transaction as recurring when the same (account, description,
    direction) repeats at least `min_occurrences` times with a similar amount
    and day-of-month. This is how the pipeline recognises a fixed salary
    credit or a monthly EMI/rent debit without depending on category labels
    — it works purely off the pattern of the raw statement data, the same
    way a real recurring-payment detector would.
    """
    groups: dict[tuple[str, str, str], list[Transaction]] = defaultdict(list)
    for t in transactions:
        groups[(t.account_id, t.description_raw, t.direction)].append(t)

    recurring_ids: set[str] = set()
    for group in groups.values():
        if len(group) < min_occurrences:
            continue
        amounts = [t.amount for t in group]
        mean_amount = sum(amounts) / len(amounts)
        if mean_amount <= 0:
            continue
        amount_spread_pct = (max(amounts) - min(amounts)) / mean_amount
        days = [date.fromisoformat(t.txn_date).day for t in group]
        day_spread = max(days) - min(days)
        if amount_spread_pct <= amount_tolerance_pct and day_spread <= day_tolerance:
            recurring_ids.update(t.id for t in group)

    return [
        t.model_copy(update={"is_recurring": True}) if t.id in recurring_ids else t
        for t in transactions
    ]
