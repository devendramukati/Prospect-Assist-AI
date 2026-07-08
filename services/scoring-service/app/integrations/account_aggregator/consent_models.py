from enum import Enum

from pydantic import BaseModel


class ConsentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class FIPInfo(BaseModel):
    """A Financial Information Provider — the other bank being pulled from."""

    fip_id: str
    name: str


class ConsentRequest(BaseModel):
    """Mirrors the RBI Account Aggregator consent artifact: purpose-bound,
    time-bound, and revocable, carrying which AA intermediary and which FIP
    (the other bank) it covers — same shape as the `consents` table planned
    for the real DB-backed version of this flow.
    """

    id: str
    customer_id: str
    external_ref: str
    aa_handle: str
    fip_id: str
    fip_name: str
    purpose: str
    status: ConsentStatus
    data_range_from: str
    data_range_to: str
    requested_at: str
    approved_at: str | None = None
    expires_at: str
    data_fetched: bool = False
