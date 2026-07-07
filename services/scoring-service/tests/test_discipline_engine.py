from app.discipline_engine.bounce_detector import detect_bounces
from app.discipline_engine.day1_velocity import compute_day1_spend_velocity
from app.discipline_engine.overdraft_detector import compute_running_balance_flags
from app.models.domain import Transaction


def _txn(id_: str, txn_date: str, amount: float, direction: str, category: str = "uncategorized",
         subcategory: str | None = None) -> Transaction:
    return Transaction(
        id=id_, account_id="a1", txn_date=txn_date, description_raw="X", amount=amount,
        direction=direction, channel="UPI", category=category, subcategory=subcategory,
    )


def test_day1_velocity_high_when_big_debit_follows_salary_immediately():
    txns = [
        _txn("s1", "2025-01-01", 80000.0, "credit"),
        _txn("d1", "2025-01-02", 68000.0, "debit"),  # 85% spent within a day
    ]
    result = compute_day1_spend_velocity(txns)
    assert result["day1_spend_velocity_pct"] > 0.8


def test_day1_velocity_low_when_spend_is_spread_across_the_month():
    txns = [
        _txn("s1", "2025-01-01", 80000.0, "credit"),
        _txn("d1", "2025-01-20", 20000.0, "debit"),
        _txn("d2", "2025-01-25", 20000.0, "debit"),
    ]
    result = compute_day1_spend_velocity(txns)
    assert result["day1_spend_velocity_pct"] < 0.1


def test_day1_velocity_handles_no_transactions():
    result = compute_day1_spend_velocity([])
    assert result["day1_spend_velocity_pct"] == 0.0
    assert result["months_observed"] == 0


def test_bounce_detector_counts_bank_charge_bounced_payment_only():
    txns = [
        _txn("b1", "2025-01-06", 590.0, "debit", category="bank_charge", subcategory="bounced_payment"),
        _txn("d1", "2025-01-10", 3200.0, "debit", category="essential_needs", subcategory="groceries"),
    ]
    result = detect_bounces(txns)
    assert result["bounce_count"] == 1
    assert result["bounce_flag"] is True


def test_bounce_detector_flags_false_when_no_bounces():
    txns = [_txn("d1", "2025-01-10", 3200.0, "debit", category="essential_needs", subcategory="groceries")]
    result = detect_bounces(txns)
    assert result["bounce_count"] == 0
    assert result["bounce_flag"] is False


def test_overdraft_detector_flags_negative_balance():
    txns = [
        _txn("d1", "2025-01-01", 5000.0, "debit"),  # spent before any credit arrived
        _txn("c1", "2025-01-05", 4000.0, "credit"),
    ]
    result = compute_running_balance_flags(txns)
    assert result["went_negative"] is True
    assert result["minimum_running_balance"] == -5000.0


def test_overdraft_detector_no_flag_when_balance_stays_healthy():
    txns = [
        _txn("c1", "2025-01-01", 80000.0, "credit"),
        _txn("d1", "2025-01-10", 20000.0, "debit"),
    ]
    result = compute_running_balance_flags(txns)
    assert result["went_negative"] is False
    assert result["low_balance_event_count"] == 0
