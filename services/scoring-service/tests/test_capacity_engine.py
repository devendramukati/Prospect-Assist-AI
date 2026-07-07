from app.capacity_engine.affordability import _max_principal_from_emi, compute_affordability
from app.capacity_engine.foir_calculator import compute_disposable_income, compute_expense_summary
from app.models.domain import Transaction


def _debit(id_: str, txn_date: str, amount: float, category: str) -> Transaction:
    return Transaction(
        id=id_, account_id="a1", txn_date=txn_date, description_raw="DEBIT", amount=amount,
        direction="debit", channel="ACH", category=category,
    )


def test_expense_summary_averages_over_all_months_observed():
    txns = [
        _debit("e1", "2025-01-05", 11000.0, "compulsory_obligation"),
        _debit("e2", "2025-02-05", 11000.0, "compulsory_obligation"),
        _debit("e3", "2025-03-05", 11000.0, "compulsory_obligation"),
        _debit("g1", "2025-01-10", 3200.0, "essential_needs"),  # only occurs in January
    ]
    summary = compute_expense_summary(txns)
    assert summary["months_observed"] == 3
    assert summary["compulsory_obligations"] == 11000.0
    # 3200 spread over all 3 observed months, not just the one month it occurred in
    assert summary["essential_needs"] == round(3200.0 / 3, 2)


def test_expense_summary_ignores_income_and_credit_transactions():
    txns = [
        Transaction(id="c1", account_id="a1", txn_date="2025-01-01", description_raw="SALARY", amount=75000.0,
                    direction="credit", channel="NEFT", category="income"),
        _debit("e1", "2025-01-05", 11000.0, "compulsory_obligation"),
    ]
    summary = compute_expense_summary(txns)
    assert summary["compulsory_obligations"] == 11000.0


def test_disposable_income_excludes_discretionary_and_savings():
    expense_summary = {
        "essential_needs": 15000.0, "compulsory_obligations": 11000.0,
        "discretionary_wants": 20000.0, "savings_investment": 25000.0,
    }
    result = compute_disposable_income(monthly_income=75000.0, expense_summary=expense_summary)
    assert result["disposable_income"] == 75000.0 - 15000.0 - 11000.0
    assert result["foir_pct"] == round(11000.0 / 75000.0, 4)


def test_disposable_income_handles_zero_income():
    result = compute_disposable_income(monthly_income=0.0, expense_summary={
        "essential_needs": 0.0, "compulsory_obligations": 0.0, "discretionary_wants": 0.0, "savings_investment": 0.0,
    })
    assert result["foir_pct"] == 0.0


def test_max_principal_from_emi_zero_rate_is_exact():
    assert _max_principal_from_emi(emi=1000.0, annual_rate_pct=0.0, tenure_months=12) == 12000.0


def test_max_principal_from_emi_zero_emi_is_zero():
    assert _max_principal_from_emi(emi=0.0, annual_rate_pct=10.0, tenure_months=60) == 0.0


def test_affordability_respects_foir_cap_and_existing_obligations():
    result = compute_affordability(monthly_income=75000.0, existing_compulsory_obligations=11000.0)
    personal_loan = result["personal_loan"]
    # personal_loan foir_cap is 0.50 in loan_products.yaml
    assert personal_loan["max_affordable_emi"] == round(0.50 * 75000.0 - 11000.0, 2)
    assert personal_loan["max_affordable_principal"] > 0


def test_affordability_floors_at_zero_when_obligations_exceed_cap():
    result = compute_affordability(monthly_income=20000.0, existing_compulsory_obligations=50000.0)
    for product in result.values():
        assert product["max_affordable_emi"] == 0.0
        assert product["max_affordable_principal"] == 0.0


def test_home_and_mortgage_flagged_as_requiring_collateral_input():
    result = compute_affordability(monthly_income=100000.0, existing_compulsory_obligations=10000.0)
    assert result["home_loan"]["requires_collateral_input"] is True
    assert result["mortgage_loan"]["requires_collateral_input"] is True
    assert result["personal_loan"]["requires_collateral_input"] is False
    assert result["auto_loan"]["requires_collateral_input"] is False
