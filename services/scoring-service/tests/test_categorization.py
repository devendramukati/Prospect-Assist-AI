from app.categorization.engine import categorize_transaction
from app.models.domain import Transaction


def _txn(description: str, amount: float = 1000.0, direction: str = "debit", channel: str = "UPI") -> Transaction:
    return Transaction(
        id="t1", account_id="a1", txn_date="2025-01-01", description_raw=description,
        amount=amount, direction=direction, channel=channel,
    )


def test_salary_credit_categorized_as_income():
    result = categorize_transaction(_txn("NEFT-SALARY-EMPLOYER PVT LTD", direction="credit", channel="NEFT"))
    assert result.category == "income"
    assert result.subcategory == "salary"
    assert result.confidence_score > 0.9


def test_grocery_debit_categorized_as_essential():
    result = categorize_transaction(_txn("BIGBAZAAR SUPERMART"))
    assert result.category == "essential_needs"
    assert result.subcategory == "groceries"


def test_home_loan_emi_categorized_as_specific_compulsory_subcategory():
    # Must not fall through to the generic "EMI" catch-all rule.
    result = categorize_transaction(_txn("ACH DEBIT-HOME LOAN EMI"))
    assert result.category == "compulsory_obligation"
    assert result.subcategory == "home_loan_emi"


def test_generic_emi_falls_back_to_other_emi_subcategory():
    result = categorize_transaction(_txn("NACH-UNKNOWN LENDER EMI"))
    assert result.category == "compulsory_obligation"
    assert result.subcategory == "other_emi"


def test_food_delivery_categorized_as_discretionary():
    result = categorize_transaction(_txn("ZOMATO ORDER"))
    assert result.category == "discretionary"
    assert result.subcategory == "food_delivery"


def test_sip_categorized_as_savings():
    result = categorize_transaction(_txn("SIP-HDFC AMC"))
    assert result.category == "savings_investment"
    assert result.subcategory == "sip"


def test_bounce_charge_categorized_as_bank_charge():
    result = categorize_transaction(_txn("ECS RET-INSUFF FUND CHARGES"))
    assert result.category == "bank_charge"
    assert result.subcategory == "bounced_payment"


def test_unknown_debit_defaults_to_uncategorized():
    result = categorize_transaction(_txn("SOME RANDOM UNKNOWN MERCHANT XYZ"))
    assert result.category == "uncategorized"
    assert result.confidence_score == 0.0


def test_unknown_credit_defaults_to_other_income():
    result = categorize_transaction(_txn("SOME UNKNOWN CREDIT SOURCE", direction="credit"))
    assert result.category == "income"
    assert result.subcategory == "other_credit"
