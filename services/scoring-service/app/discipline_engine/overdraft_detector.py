from app.models.domain import Transaction


def compute_running_balance_flags(transactions: list[Transaction], low_balance_threshold: float = 1000.0) -> dict:
    """Simulates a running balance across the statement period (assuming an
    opening balance of 0, since the raw statement only gives transaction
    deltas, not the true opening balance) and flags any point where it dips
    below a low-balance threshold or goes negative. This is a general
    cash-flow-crunch signal, independent of whether the bank has already
    logged an explicit bounce charge for the same event.
    """
    ordered = sorted(transactions, key=lambda t: t.txn_date)
    balance = 0.0
    min_balance = 0.0
    low_balance_event_count = 0

    for t in ordered:
        balance += t.amount if t.direction == "credit" else -t.amount
        min_balance = min(min_balance, balance)
        if balance < low_balance_threshold:
            low_balance_event_count += 1

    return {
        "minimum_running_balance": round(min_balance, 2),
        "low_balance_event_count": low_balance_event_count,
        "went_negative": min_balance < 0,
    }
