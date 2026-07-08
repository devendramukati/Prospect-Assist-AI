from abc import ABC, abstractmethod

from pydantic import BaseModel


class KYCProfile(BaseModel):
    full_name: str
    pan_masked: str
    phone_masked: str
    date_of_birth: str


class CoreBankingClient(ABC):
    """Realistic stub for a Finacle/Flexcube/BaNCS-style core banking API.
    A customer's registered name/PAN/phone lives in core banking/KYC
    records, not the bank statement itself — this is the interface the rest
    of the app depends on to enrich a pseudonymous external_ref with a
    display-ready identity, without the analytics pipeline ever needing to
    touch raw PII directly.
    """

    @abstractmethod
    def get_kyc_profile(self, external_ref: str) -> KYCProfile:
        raise NotImplementedError
