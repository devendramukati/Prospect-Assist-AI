from fastapi import APIRouter, HTTPException

from app.categorization.engine import categorize_transactions
from app.categorization.recurring_detector import detect_recurring
from app.core.config import settings
from app.ingestion.synthetic_source import SyntheticFileIngestionSource

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/{external_ref}/categorized-transactions")
def get_categorized_transactions(external_ref: str) -> dict:
    source = SyntheticFileIngestionSource(settings.synthetic_data_dir)
    try:
        bundle = source.load(external_ref)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    statements_out = []
    for statement in bundle.statements:
        categorized = categorize_transactions(statement.transactions)
        categorized = detect_recurring(categorized)
        statements_out.append(
            {
                "account_id": statement.account_id,
                "transactions": [t.model_dump() for t in categorized],
            }
        )

    return {"customer": bundle.customer.model_dump(), "statements": statements_out}
