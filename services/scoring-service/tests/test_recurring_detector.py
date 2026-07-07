from app.categorization.recurring_detector import detect_recurring
from app.models.domain import Transaction


def _txn(id_: str, description: str, amount: float, txn_date: str, direction: str = "debit") -> Transaction:
    return Transaction(
        id=id_, account_id="a1", txn_date=txn_date, description_raw=description,
        amount=amount, direction=direction, channel="ACH",
    )


def test_recurring_emi_flagged_across_three_months():
    txns = [
        _txn("e1", "ACH DEBIT-HOME LOAN EMI", 11000.0, "2025-01-05"),
        _txn("e2", "ACH DEBIT-HOME LOAN EMI", 11050.0, "2025-02-05"),
        _txn("e3", "ACH DEBIT-HOME LOAN EMI", 10980.0, "2025-03-05"),
    ]
    result = detect_recurring(txns)
    assert all(t.is_recurring for t in result)


def test_one_off_transaction_not_flagged_recurring():
    txns = [
        _txn("e1", "ACH DEBIT-HOME LOAN EMI", 11000.0, "2025-01-05"),
        _txn("e2", "ACH DEBIT-HOME LOAN EMI", 11050.0, "2025-02-05"),
        _txn("g1", "BIGBAZAAR SUPERMART", 3200.0, "2025-01-10"),
    ]
    result = detect_recurring(txns)
    by_id = {t.id: t for t in result}
    assert not by_id["g1"].is_recurring
    # only two occurrences (below min_occurrences=3), so the EMI shouldn't be flagged either
    assert not by_id["e1"].is_recurring


def test_volatile_amount_not_flagged_recurring():
    txns = [
        _txn("g1", "ZOMATO ORDER", 300.0, "2025-01-10"),
        _txn("g2", "ZOMATO ORDER", 1200.0, "2025-02-15"),
        _txn("g3", "ZOMATO ORDER", 50.0, "2025-03-20"),
    ]
    result = detect_recurring(txns)
    assert not any(t.is_recurring for t in result)


def test_different_accounts_are_not_grouped_together():
    txns = [
        Transaction(id="a1", account_id="acct-1", txn_date="2025-01-05", description_raw="ACH DEBIT-HOME LOAN EMI",
                    amount=11000.0, direction="debit", channel="ACH"),
        Transaction(id="a2", account_id="acct-2", txn_date="2025-02-05", description_raw="ACH DEBIT-HOME LOAN EMI",
                    amount=11000.0, direction="debit", channel="ACH"),
        Transaction(id="a3", account_id="acct-1", txn_date="2025-03-05", description_raw="ACH DEBIT-HOME LOAN EMI",
                    amount=11000.0, direction="debit", channel="ACH"),
    ]
    result = detect_recurring(txns)
    assert not any(t.is_recurring for t in result)
