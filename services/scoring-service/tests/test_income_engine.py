import pytest

from app.income_engine.business_owner import estimate_business_income
from app.income_engine.gig_irregular import estimate_gig_income
from app.income_engine.router import estimate_income
from app.income_engine.salaried import estimate_salaried_income
from app.models.domain import Transaction


def _credit(id_: str, month_day: str, amount: float, subcategory: str, is_recurring: bool = False) -> Transaction:
    return Transaction(
        id=id_, account_id="a1", txn_date=month_day, description_raw="CREDIT", amount=amount,
        direction="credit", channel="NEFT", category="income", subcategory=subcategory, is_recurring=is_recurring,
    )


def test_salaried_income_uses_median_and_high_stability_for_low_variance():
    txns = [
        _credit("s1", "2025-01-01", 75000.0, "salary", is_recurring=True),
        _credit("s2", "2025-02-01", 75500.0, "salary", is_recurring=True),
        _credit("s3", "2025-03-01", 74800.0, "salary", is_recurring=True),
    ]
    result = estimate_salaried_income(txns)
    assert result["method"] == "fixed_salary"
    assert 74800 <= result["monthly_income_estimate"] <= 75500
    assert result["income_stability_score"] > 0.8


def test_salaried_income_falls_back_when_no_recurring_flag_present():
    txns = [_credit("s1", "2025-01-01", 75000.0, "salary", is_recurring=False)]
    result = estimate_salaried_income(txns)
    assert result["sample_size"] == 1
    assert result["monthly_income_estimate"] == 75000.0


def test_salaried_income_empty_when_no_salary_transactions():
    result = estimate_salaried_income([])
    assert result["monthly_income_estimate"] == 0.0
    assert result["sample_size"] == 0


def test_gig_income_discounts_high_volatility():
    stable_txns = [
        _credit("g1", "2025-01-15", 40000.0, "gig_payout"),
        _credit("g2", "2025-02-15", 40500.0, "gig_payout"),
        _credit("g3", "2025-03-15", 39500.0, "gig_payout"),
    ]
    volatile_txns = [
        _credit("v1", "2025-01-15", 10000.0, "gig_payout"),
        _credit("v2", "2025-02-15", 70000.0, "gig_payout"),
        _credit("v3", "2025-03-15", 15000.0, "gig_payout"),
    ]
    stable_result = estimate_gig_income(stable_txns)
    volatile_result = estimate_gig_income(volatile_txns)

    assert stable_result["income_stability_score"] > volatile_result["income_stability_score"]
    # discounted estimate should sit meaningfully below the simple monthly average for a volatile earner
    volatile_avg = (10000.0 + 70000.0 + 15000.0) / 3
    assert volatile_result["monthly_income_estimate"] < volatile_avg


def test_business_income_returns_confidence_band_not_single_number():
    txns = [_credit(f"b{i}", "2025-01-01", 15000.0, "business_turnover") for i in range(60)]
    result = estimate_business_income(txns, industry="retail_trade")
    assert result["monthly_income_estimate_low"] < result["monthly_income_estimate_mid"] < result["monthly_income_estimate_high"]
    assert result["monthly_turnover"] == 900000.0


def test_business_income_uses_default_band_for_unknown_industry():
    txns = [_credit("b1", "2025-01-01", 100000.0, "business_turnover")]
    result = estimate_business_income(txns, industry="some_unlisted_industry")
    assert result["monthly_income_estimate_low"] > 0


def test_router_dispatches_by_employment_type():
    salary_txns = [_credit("s1", "2025-01-01", 75000.0, "salary", is_recurring=True)]
    gig_txns = [_credit("g1", "2025-01-01", 40000.0, "gig_payout")]
    business_txns = [_credit("b1", "2025-01-01", 900000.0, "business_turnover")]

    salaried_estimate = estimate_income("salaried", salary_txns)
    assert salaried_estimate.method == "fixed_salary"
    assert salaried_estimate.confidence_low is None

    gig_estimate = estimate_income("gig", gig_txns)
    assert gig_estimate.method == "rolling_avg"

    business_estimate = estimate_income("business_owner", business_txns)
    assert business_estimate.method == "turnover_margin"
    assert business_estimate.confidence_low is not None
    assert business_estimate.confidence_high is not None

    self_employed_estimate = estimate_income("self_employed", business_txns)
    assert self_employed_estimate.method == "turnover_margin"


def test_router_raises_for_unknown_employment_type():
    with pytest.raises(ValueError):
        estimate_income("astronaut", [])
