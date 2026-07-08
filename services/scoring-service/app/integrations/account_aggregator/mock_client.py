import random
import uuid
from datetime import date, datetime, timedelta, timezone

from app.integrations.account_aggregator.base import AAClient
from app.integrations.account_aggregator.consent_models import ConsentRequest, ConsentStatus, FIPInfo
from app.models.domain import BankAccount, Statement, Transaction

MOCK_FIPS = [
    FIPInfo(fip_id="HDFC-FIP", name="HDFC Bank"),
    FIPInfo(fip_id="ICICI-FIP", name="ICICI Bank"),
    FIPInfo(fip_id="SBI-FIP", name="State Bank of India"),
    FIPInfo(fip_id="AXIS-FIP", name="Axis Bank"),
]
_FIP_NAMES = {fip.fip_id: fip.name for fip in MOCK_FIPS}

DEFAULT_AA_HANDLE = "customer@finvu"
DEFAULT_PURPOSE = "Income verification for loan underwriting"
CONSENT_VALIDITY_DAYS = 30
STATEMENT_PERIOD_MONTHS = 6


class MockAAClient(AAClient):
    """In-memory stand-in for a licensed Account Aggregator. State resets
    when the process restarts — acceptable for this MVP demo since no
    database is wired up yet; the real version persists to the `consents`
    table and calls out to Sahamati-network APIs (see docs/aws-migration-map.md).
    """

    def __init__(self) -> None:
        self._consents: dict[str, ConsentRequest] = {}
        self._fetched_data: dict[str, tuple[BankAccount, Statement]] = {}

    def list_fips(self) -> list[FIPInfo]:
        return MOCK_FIPS

    def create_consent_request(
        self,
        customer_id: str,
        external_ref: str,
        fip_id: str,
        purpose: str = DEFAULT_PURPOSE,
        data_range_from: str | None = None,
        data_range_to: str | None = None,
    ) -> ConsentRequest:
        """data_range_from/to should normally be the caller's existing
        primary-account statement span, not left to default — the linked
        account's generated months must line up with the primary account's
        months for consolidation to sum correctly rather than averaging in
        a run of non-overlapping low-income months.
        """
        if fip_id not in _FIP_NAMES:
            raise ValueError(f"Unknown fip_id: {fip_id}")

        now = datetime.now(timezone.utc)
        data_to = date.fromisoformat(data_range_to) if data_range_to else date.today()
        data_from = (
            date.fromisoformat(data_range_from) if data_range_from else data_to - timedelta(days=30 * STATEMENT_PERIOD_MONTHS)
        )

        consent = ConsentRequest(
            id=f"consent_{uuid.uuid4().hex[:12]}",
            customer_id=customer_id,
            external_ref=external_ref,
            aa_handle=DEFAULT_AA_HANDLE,
            fip_id=fip_id,
            fip_name=_FIP_NAMES[fip_id],
            purpose=purpose,
            status=ConsentStatus.PENDING,
            data_range_from=data_from.isoformat(),
            data_range_to=data_to.isoformat(),
            requested_at=now.isoformat(),
            expires_at=(now + timedelta(days=CONSENT_VALIDITY_DAYS)).isoformat(),
        )
        self._consents[consent.id] = consent
        return consent

    def approve_consent(self, consent_id: str) -> ConsentRequest:
        consent = self._require(consent_id)
        consent.status = ConsentStatus.APPROVED
        consent.approved_at = datetime.now(timezone.utc).isoformat()
        return consent

    def deny_consent(self, consent_id: str) -> ConsentRequest:
        consent = self._require(consent_id)
        consent.status = ConsentStatus.DENIED
        return consent

    def get_consent(self, consent_id: str) -> ConsentRequest:
        return self._require(consent_id)

    def list_consents_for_customer(self, external_ref: str) -> list[ConsentRequest]:
        return [c for c in self._consents.values() if c.external_ref == external_ref]

    def fetch_fi_data(self, consent_id: str) -> tuple[BankAccount, Statement]:
        consent = self._require(consent_id)
        if consent.status != ConsentStatus.APPROVED:
            raise ValueError(f"Cannot fetch data for consent in status {consent.status.value!r}; must be approved")

        if consent_id not in self._fetched_data:
            self._fetched_data[consent_id] = self._generate_linked_account(consent)
        consent.data_fetched = True
        return self._fetched_data[consent_id]

    def get_fetched_data(self, consent_id: str) -> tuple[BankAccount, Statement]:
        if consent_id not in self._fetched_data:
            raise KeyError(f"No fetched data for consent_id: {consent_id}")
        return self._fetched_data[consent_id]

    def _require(self, consent_id: str) -> ConsentRequest:
        if consent_id not in self._consents:
            raise KeyError(f"Unknown consent_id: {consent_id}")
        return self._consents[consent_id]

    def _generate_linked_account(self, consent: ConsentRequest) -> tuple[BankAccount, Statement]:
        """Fabricates a plausible secondary account with its own modest
        income stream, deterministic per consent id. This is a small,
        self-contained generator (not a dependency on
        packages/synthetic-data-generator) so the scoring service has no
        cross-package coupling in its deployed Docker image.
        """
        rng = random.Random(f"aa-{consent.id}")
        account_id = f"acct_aa_{rng.getrandbits(32):08x}"

        account = BankAccount(
            id=account_id,
            customer_id=consent.customer_id,
            bank_name=consent.fip_name,
            masked_account_number=f"XXXXXXXX{rng.randint(1000, 9999)}",
            source="aa_pull",
        )

        # Walk the exact inclusive month range requested, not a fixed
        # lookback — this must line up with the primary account's own
        # statement months for consolidation to sum correctly per month
        # rather than averaging in a run of non-overlapping months.
        range_from = date.fromisoformat(consent.data_range_from).replace(day=1)
        range_to = date.fromisoformat(consent.data_range_to).replace(day=1)
        month_starts = []
        year, month = range_from.year, range_from.month
        while (year, month) <= (range_to.year, range_to.month):
            month_starts.append(date(year, month, 1))
            month += 1
            if month > 12:
                month = 1
                year += 1

        # A stable base with small month-to-month variance (like a real
        # salary) rather than a fresh wide-range draw each month — the
        # recurring-transaction detector (Phase 2) requires amounts within
        # 25% of each other to recognize a repeating credit as recurring,
        # and only recurring credits feed the salaried income estimate.
        base_amount = rng.uniform(15000, 25000)

        transactions = []
        for month_start in month_starts:
            credit_amount = round(base_amount * (1 + rng.uniform(-0.05, 0.05)), 2)
            transactions.append(
                Transaction(
                    id=f"txn_aa_{rng.getrandbits(48):012x}",
                    account_id=account_id,
                    txn_date=month_start.replace(day=1).isoformat(),
                    description_raw="NEFT-SALARY-EMPLOYER PVT LTD",
                    amount=credit_amount,
                    direction="credit",
                    channel="NEFT",
                )
            )
            savings_day = min(25, 28)
            transactions.append(
                Transaction(
                    id=f"txn_aa_{rng.getrandbits(48):012x}",
                    account_id=account_id,
                    txn_date=month_start.replace(day=savings_day).isoformat(),
                    description_raw="SIP-HDFC AMC",
                    amount=round(credit_amount * 0.3, 2),
                    direction="debit",
                    channel="UPI",
                )
            )

        statement = Statement(
            account_id=account_id,
            period_start=month_starts[0].isoformat(),
            period_end=month_starts[-1].isoformat(),
            transactions=transactions,
        )
        return account, statement


_default_client = MockAAClient()


def get_aa_client() -> MockAAClient:
    return _default_client
