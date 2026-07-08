from fastapi import APIRouter, Depends, HTTPException

from app.capacity_engine.affordability import compute_affordability
from app.capacity_engine.foir_calculator import compute_disposable_income, compute_expense_summary
from app.categorization.engine import categorize_transactions
from app.categorization.recurring_detector import detect_recurring
from app.core.config import settings
from app.discipline_engine.bounce_detector import detect_bounces
from app.discipline_engine.day1_velocity import compute_day1_spend_velocity
from app.discipline_engine.overdraft_detector import compute_running_balance_flags
from app.income_engine.router import estimate_income
from app.ingestion.synthetic_source import SyntheticFileIngestionSource
from app.integrations.account_aggregator.base import AAClient
from app.integrations.account_aggregator.consent_models import ConsentStatus
from app.integrations.account_aggregator.mock_client import get_aa_client
from app.models.domain import CustomerBundle, Transaction

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _load_and_categorize_by_account(external_ref: str, aa_client: AAClient) -> tuple[CustomerBundle, list[dict]]:
    source = SyntheticFileIngestionSource(settings.synthetic_data_dir)
    bundle = source.load(external_ref)

    statements_out = []
    for statement in bundle.statements:
        categorized = categorize_transactions(statement.transactions)
        categorized = detect_recurring(categorized)
        statements_out.append({"account_id": statement.account_id, "transactions": categorized})

    # Any Account Aggregator consent that's been approved and fetched adds
    # another account/statement into the same customer's picture — this is
    # the mechanism behind the "consolidated capacity assessment" the AA
    # linking flow (Phase 6) promises, without any DB required for the MVP.
    for consent in aa_client.list_consents_for_customer(external_ref):
        if consent.status == ConsentStatus.APPROVED and consent.data_fetched:
            linked_account, linked_statement = aa_client.get_fetched_data(consent.id)
            bundle.accounts.append(linked_account)
            categorized = categorize_transactions(linked_statement.transactions)
            categorized = detect_recurring(categorized)
            statements_out.append({"account_id": linked_account.id, "transactions": categorized})

    return bundle, statements_out


def _load_and_categorize_flat(external_ref: str, aa_client: AAClient) -> tuple[CustomerBundle, list[Transaction]]:
    """Flattens categorized transactions across all of a customer's
    accounts, since repayment capacity should reflect the customer's whole
    cash flow regardless of which account a transaction landed in — this is
    also what makes the multi-account archetype's consolidated assessment
    work without any extra wiring.
    """
    bundle, statements_out = _load_and_categorize_by_account(external_ref, aa_client)
    all_transactions = [t for statement in statements_out for t in statement["transactions"]]
    return bundle, all_transactions


@router.get("/{external_ref}/categorized-transactions")
def get_categorized_transactions(external_ref: str, aa_client: AAClient = Depends(get_aa_client)) -> dict:
    try:
        bundle, statements_out = _load_and_categorize_by_account(external_ref, aa_client)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "customer": bundle.customer.model_dump(),
        "statements": [
            {"account_id": s["account_id"], "transactions": [t.model_dump() for t in s["transactions"]]}
            for s in statements_out
        ],
    }


def build_capacity_assessment(customer_employment_type: str, transactions: list[Transaction]) -> dict:
    """Runs the full Phase 3 income/capacity/discipline pipeline for one
    customer's flattened transactions. Shared by the /capacity-assessment
    endpoint and the /leads scoring endpoints so both compute this from a
    single source of truth.
    """
    income = estimate_income(customer_employment_type, transactions)
    expense_summary = compute_expense_summary(transactions)

    # For a business/turnover-based income estimate, existing obligations and
    # spend categories were incurred against the business's gross cash flow
    # (turnover), not the owner's margin-adjusted personal take-home — so
    # FOIR/disposable-income/affordability must be assessed against that same
    # turnover basis (a cash-flow/DSCR-style view), while the net-income band
    # in `income` stays available separately for personal-loan-style context.
    capacity_basis = "net_income"
    capacity_base_income = income.monthly_income_estimate
    if income.method == "turnover_margin":
        capacity_basis = "turnover"
        capacity_base_income = income.supporting_evidence.get("monthly_turnover", income.monthly_income_estimate)

    disposable = compute_disposable_income(capacity_base_income, expense_summary)
    affordability = compute_affordability(capacity_base_income, expense_summary["compulsory_obligations"])

    return {
        "income": income.model_dump(),
        "expense_summary": expense_summary,
        "capacity_basis": capacity_basis,
        "capacity_base_income": capacity_base_income,
        "disposable_income": disposable,
        "affordability_by_product": affordability,
        "discipline": {
            "day1_spend_velocity": compute_day1_spend_velocity(transactions),
            "bounce": detect_bounces(transactions),
            "balance": compute_running_balance_flags(transactions),
        },
    }


@router.get("/{external_ref}/capacity-assessment")
def get_capacity_assessment(external_ref: str, aa_client: AAClient = Depends(get_aa_client)) -> dict:
    try:
        bundle, transactions = _load_and_categorize_flat(external_ref, aa_client)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    assessment = build_capacity_assessment(bundle.customer.employment_type, transactions)
    return {"customer": bundle.customer.model_dump(), **assessment}
