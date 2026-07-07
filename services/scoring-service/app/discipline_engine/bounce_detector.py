from app.models.domain import Transaction


def detect_bounces(transactions: list[Transaction]) -> dict:
    """Counts bounced-payment charges the categorization engine already
    identified (ECS RET / insufficient-funds narrations) — a direct,
    unambiguous signal a scheduled obligation failed to clear.
    """
    bounce_txns = [t for t in transactions if t.category == "bank_charge" and t.subcategory == "bounced_payment"]
    return {
        "bounce_count": len(bounce_txns),
        "bounce_flag": len(bounce_txns) > 0,
    }
