from fastapi import APIRouter, HTTPException

from app.api.routes.pipeline import _load_and_categorize_flat, build_capacity_assessment
from app.core.config import settings
from app.ingestion.synthetic_source import SyntheticFileIngestionSource
from app.scoring_engine.composite_scorer import compute_composite_score

router = APIRouter(prefix="/leads", tags=["leads"])


def _score_customer(external_ref: str) -> dict:
    bundle, transactions = _load_and_categorize_flat(external_ref)
    assessment = build_capacity_assessment(bundle.customer.employment_type, transactions)
    score = compute_composite_score(bundle.application_events, assessment)
    return {"customer": bundle.customer.model_dump(), "assessment": assessment, "score": score}


@router.get("")
def list_leads() -> dict:
    source = SyntheticFileIngestionSource(settings.synthetic_data_dir)
    leads = []
    for external_ref in source.list_external_refs():
        result = _score_customer(external_ref)
        leads.append(
            {
                "external_ref": external_ref,
                "employment_type": result["customer"]["employment_type"],
                "tier": result["score"]["tier"],
                "composite_score": result["score"]["composite_score"],
                "capped_by": result["score"]["capped_by"],
            }
        )

    leads.sort(key=lambda lead: lead["composite_score"], reverse=True)
    return {"count": len(leads), "leads": leads}


@router.get("/{external_ref}/explain")
def explain_lead(external_ref: str) -> dict:
    try:
        return _score_customer(external_ref)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
