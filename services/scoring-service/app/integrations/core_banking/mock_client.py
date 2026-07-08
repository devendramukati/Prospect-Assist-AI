import random

from app.integrations.core_banking.base import CoreBankingClient, KYCProfile

FIRST_NAMES = ["Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Sneha", "Karan", "Divya", "Aditya", "Meera"]
LAST_NAMES = ["Sharma", "Patel", "Reddy", "Iyer", "Singh", "Gupta", "Nair", "Verma", "Joshi", "Menon"]
PAN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class MockCoreBankingClient(CoreBankingClient):
    """Deterministically fabricates a plausible KYC profile per external_ref
    (same input always yields the same output) since no real KYC data
    exists for synthetic customers — bank statements alone never carry a
    customer's registered name/PAN/phone.
    """

    def get_kyc_profile(self, external_ref: str) -> KYCProfile:
        rng = random.Random(f"kyc-{external_ref}")
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        pan_middle = "".join(rng.choices(PAN_LETTERS, k=4))
        pan_digits = rng.randint(1000, 9999)

        return KYCProfile(
            full_name=f"{first_name} {last_name}",
            pan_masked=f"XXXXX{pan_middle[:2]}{pan_digits}X",
            phone_masked=f"XXXXXX{rng.randint(1000, 9999)}",
            date_of_birth=f"{rng.randint(1970, 2000)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
        )


_default_client = MockCoreBankingClient()


def get_core_banking_client() -> MockCoreBankingClient:
    return _default_client
