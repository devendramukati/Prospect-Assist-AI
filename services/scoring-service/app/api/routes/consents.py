from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.audit import record_audit_event
from app.core.config import settings
from app.ingestion.synthetic_source import SyntheticFileIngestionSource
from app.integrations.account_aggregator.base import AAClient
from app.integrations.account_aggregator.mock_client import DEFAULT_PURPOSE, get_aa_client

router = APIRouter(prefix="/consents", tags=["consents"])


class ConsentCreateRequest(BaseModel):
    fip_id: str
    purpose: str = DEFAULT_PURPOSE


@router.get("/fips")
def list_fips(aa_client: AAClient = Depends(get_aa_client)) -> dict:
    return {"fips": [fip.model_dump() for fip in aa_client.list_fips()]}


@router.get("/{external_ref}")
def list_consents_for_customer(external_ref: str, aa_client: AAClient = Depends(get_aa_client)) -> dict:
    consents = aa_client.list_consents_for_customer(external_ref)
    return {"consents": [c.model_dump() for c in consents]}


@router.post("/{external_ref}/request")
def request_consent(
    external_ref: str, body: ConsentCreateRequest, aa_client: AAClient = Depends(get_aa_client)
) -> dict:
    source = SyntheticFileIngestionSource(settings.synthetic_data_dir)
    try:
        bundle = source.load(external_ref)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Align the pulled account's statement months with the customer's
    # existing primary-account months, so consolidation sums per month
    # instead of averaging in a run of non-overlapping months.
    data_range_from = min((s.period_start for s in bundle.statements), default=None)
    data_range_to = max((s.period_end for s in bundle.statements), default=None)

    try:
        consent = aa_client.create_consent_request(
            customer_id=bundle.customer.id,
            external_ref=external_ref,
            fip_id=body.fip_id,
            purpose=body.purpose,
            data_range_from=data_range_from,
            data_range_to=data_range_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    record_audit_event(
        entity_type="consent",
        entity_id=consent.id,
        action="requested",
        metadata={"external_ref": external_ref, "fip_id": body.fip_id, "purpose": body.purpose},
    )
    return consent.model_dump()


@router.post("/{consent_id}/approve")
def approve_consent(consent_id: str, aa_client: AAClient = Depends(get_aa_client)) -> dict:
    try:
        consent = aa_client.approve_consent(consent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(entity_type="consent", entity_id=consent.id, action="approved")
    return consent.model_dump()


@router.post("/{consent_id}/deny")
def deny_consent(consent_id: str, aa_client: AAClient = Depends(get_aa_client)) -> dict:
    try:
        consent = aa_client.deny_consent(consent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_audit_event(entity_type="consent", entity_id=consent.id, action="denied")
    return consent.model_dump()


@router.post("/{consent_id}/fetch")
def fetch_consent_data(consent_id: str, aa_client: AAClient = Depends(get_aa_client)) -> dict:
    try:
        account, statement = aa_client.fetch_fi_data(consent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record_audit_event(
        entity_type="consent",
        entity_id=consent_id,
        action="fetched",
        metadata={"linked_account_id": account.id, "transaction_count": len(statement.transactions)},
    )
    return {"account": account.model_dump(), "statement": statement.model_dump()}
