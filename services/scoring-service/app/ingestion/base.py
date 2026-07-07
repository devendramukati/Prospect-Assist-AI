from abc import ABC, abstractmethod

from app.models.domain import CustomerBundle


class IngestionSource(ABC):
    """Pulls one customer's account/statement/funnel-event data from wherever
    it originates (synthetic fixtures, an uploaded PDF, or an Account
    Aggregator consent pull). Downstream categorization and scoring code
    depends only on this interface, so the data source can be swapped
    (synthetic -> PDF -> real AA pull) without touching anything downstream.
    """

    @abstractmethod
    def load(self, external_ref: str) -> CustomerBundle:
        raise NotImplementedError
