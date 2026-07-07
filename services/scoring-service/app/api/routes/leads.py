from fastapi import APIRouter, HTTPException

from app.api.routes.pipeline import _load_and_categorize_flat, build_capacity_assessment
from app.core.config import settings
from app.ingestion.synthetic_source import SyntheticFileIngestionSource
from app.scoring_engine.composite_scorer import compute_composite_score
from app.scoring_engine.intent_scorer import compute_intent_score
from app.scoring_engine.tiering import DISCIPLINE_RED_FLAG_DAY1_THRESHOLD
from app.underwriting.report_builder import build_underwriting_report

router = APIRouter(prefix="/leads", tags=["leads"])


def _score_customer(external_ref: str) -> dict:
    bundle, transactions = _load_and_categorize_flat(external_ref)
    assessment = build_capacity_assessment(bundle.customer.employment_type, transactions)
    score = compute_composite_score(bundle.application_events, assessment)
    intent = compute_intent_score(bundle.application_events)
    return {"customer": bundle.customer.model_dump(), "assessment": assessment, "score": score, "intent": intent}


def _is_discipline_flagged(assessment: dict) -> bool:
    discipline = assessment["discipline"]
    day1_pct = discipline["day1_spend_velocity"]["day1_spend_velocity_pct"]
    return discipline["bounce"]["bounce_flag"] or day1_pct >= DISCIPLINE_RED_FLAG_DAY1_THRESHOLD


@router.get("")
def list_leads() -> dict:
    """Summary used by the dashboard/leads-table — includes enough (max_stage,
    reached_disbursed, discipline_flagged) to compute conversion and
    discipline-flag-rate KPIs from a single call, without an N+1 fetch per lead.
    """
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
                "max_stage": result["intent"]["max_stage"],
                "reached_disbursed": result["intent"]["max_stage"] == "disbursed",
                "discipline_flagged": _is_discipline_flagged(result["assessment"]),
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


@router.get("/{external_ref}/underwriting-report")
def get_underwriting_report(external_ref: str) -> dict:
    try:
        result = _score_customer(external_ref)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return build_underwriting_report(result["customer"], result["assessment"], result["score"])
