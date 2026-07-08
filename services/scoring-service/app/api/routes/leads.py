from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.pipeline import _load_and_categorize_flat, build_capacity_assessment
from app.core.audit import record_audit_event
from app.core.config import settings
from app.ingestion.synthetic_source import SyntheticFileIngestionSource
from app.integrations.account_aggregator.base import AAClient
from app.integrations.account_aggregator.mock_client import get_aa_client
from app.integrations.core_banking.base import CoreBankingClient
from app.integrations.core_banking.mock_client import get_core_banking_client
from app.scoring_engine.composite_scorer import compute_composite_score
from app.scoring_engine.intent_scorer import compute_intent_score
from app.scoring_engine.tiering import DISCIPLINE_RED_FLAG_DAY1_THRESHOLD
from app.underwriting.report_builder import build_underwriting_report

router = APIRouter(prefix="/leads", tags=["leads"])


def _score_customer(external_ref: str, aa_client: AAClient, core_banking_client: CoreBankingClient) -> dict:
    bundle, transactions = _load_and_categorize_flat(external_ref, aa_client)
    assessment = build_capacity_assessment(bundle.customer.employment_type, transactions)
    score = compute_composite_score(bundle.application_events, assessment)
    intent = compute_intent_score(bundle.application_events)

    customer = bundle.customer.model_dump()
    customer["kyc"] = core_banking_client.get_kyc_profile(external_ref).model_dump()
    customer["account_count"] = len(bundle.accounts)

    return {"customer": customer, "assessment": assessment, "score": score, "intent": intent}


def _is_discipline_flagged(assessment: dict) -> bool:
    discipline = assessment["discipline"]
    day1_pct = discipline["day1_spend_velocity"]["day1_spend_velocity_pct"]
    return discipline["bounce"]["bounce_flag"] or day1_pct >= DISCIPLINE_RED_FLAG_DAY1_THRESHOLD


@router.get("")
def list_leads(
    aa_client: AAClient = Depends(get_aa_client),
    core_banking_client: CoreBankingClient = Depends(get_core_banking_client),
) -> dict:
    """Summary used by the dashboard/leads-table — includes enough (max_stage,
    reached_disbursed, discipline_flagged) to compute conversion and
    discipline-flag-rate KPIs from a single call, without an N+1 fetch per lead.
    """
    source = SyntheticFileIngestionSource(settings.synthetic_data_dir)
    leads = []
    for external_ref in source.list_external_refs():
        result = _score_customer(external_ref, aa_client, core_banking_client)
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
def explain_lead(
    external_ref: str,
    aa_client: AAClient = Depends(get_aa_client),
    core_banking_client: CoreBankingClient = Depends(get_core_banking_client),
) -> dict:
    try:
        return _score_customer(external_ref, aa_client, core_banking_client)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{external_ref}/underwriting-report")
def get_underwriting_report(
    external_ref: str,
    aa_client: AAClient = Depends(get_aa_client),
    core_banking_client: CoreBankingClient = Depends(get_core_banking_client),
) -> dict:
    try:
        result = _score_customer(external_ref, aa_client, core_banking_client)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    report = build_underwriting_report(result["customer"], result["assessment"], result["score"])
    record_audit_event(
        entity_type="underwriting_report",
        entity_id=external_ref,
        action="generated",
        metadata={"tier": report["lead_tier"], "composite_score": report["composite_score"]},
    )
    return report
