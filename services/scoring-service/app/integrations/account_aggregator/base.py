from abc import ABC, abstractmethod

from app.integrations.account_aggregator.consent_models import ConsentRequest, FIPInfo
from app.models.domain import BankAccount, Statement


class AAClient(ABC):
    """Models the RBI-regulated Account Aggregator consent flow (Sahamati
    network; licensed AAs like Finvu/OneMoney/CAMSFinserv/Anumati) — the
    realistic, consent-based mechanism a bank uses to pull a customer's
    OTHER bank statements, instead of asking the customer to manually
    upload another PDF. A real implementation would call the AA's consent
    and FI-data-fetch APIs and decrypt the response with the FIU's private
    key; this interface is what the rest of the app depends on either way.
    """

    @abstractmethod
    def list_fips(self) -> list[FIPInfo]:
        raise NotImplementedError

    @abstractmethod
    def create_consent_request(
        self,
        customer_id: str,
        external_ref: str,
        fip_id: str,
        purpose: str,
        data_range_from: str | None = None,
        data_range_to: str | None = None,
    ) -> ConsentRequest:
        raise NotImplementedError

    @abstractmethod
    def approve_consent(self, consent_id: str) -> ConsentRequest:
        raise NotImplementedError

    @abstractmethod
    def deny_consent(self, consent_id: str) -> ConsentRequest:
        raise NotImplementedError

    @abstractmethod
    def get_consent(self, consent_id: str) -> ConsentRequest:
        raise NotImplementedError

    @abstractmethod
    def list_consents_for_customer(self, external_ref: str) -> list[ConsentRequest]:
        raise NotImplementedError

    @abstractmethod
    def fetch_fi_data(self, consent_id: str) -> tuple[BankAccount, Statement]:
        raise NotImplementedError

    @abstractmethod
    def get_fetched_data(self, consent_id: str) -> tuple[BankAccount, Statement]:
        raise NotImplementedError
