from app.ingestion.base import IngestionSource
from app.models.domain import CustomerBundle


class AccountAggregatorIngestionSource(IngestionSource):
    """Stub for a real RBI-regulated Account Aggregator consent-based pull
    (Sahamati network; licensed AAs like Finvu/OneMoney/CAMSFinserv/Anumati).
    This is the realistic mechanism for the "ask for another bank statement"
    multi-account requirement — Phase 6 adds the mock AAClient and consent
    flow this will call.
    """

    def load(self, external_ref: str) -> CustomerBundle:
        raise NotImplementedError("Account Aggregator ingestion lands in Phase 6")
