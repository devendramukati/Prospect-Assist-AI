import pytest

from app.integrations.account_aggregator.consent_models import ConsentStatus
from app.integrations.account_aggregator.mock_client import MockAAClient


@pytest.fixture
def aa_client() -> MockAAClient:
    return MockAAClient()


def test_list_fips_returns_known_banks(aa_client):
    fips = aa_client.list_fips()
    assert len(fips) >= 2
    assert all(fip.fip_id and fip.name for fip in fips)


def test_create_consent_request_starts_pending(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    assert consent.status == ConsentStatus.PENDING
    assert consent.fip_name == "HDFC Bank"
    assert consent.data_fetched is False


def test_create_consent_request_rejects_unknown_fip(aa_client):
    with pytest.raises(ValueError):
        aa_client.create_consent_request("cust_1", "demo-001", "UNKNOWN-FIP", "Loan underwriting")


def test_approve_consent_transitions_status(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    approved = aa_client.approve_consent(consent.id)
    assert approved.status == ConsentStatus.APPROVED
    assert approved.approved_at is not None


def test_deny_consent_transitions_status(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    denied = aa_client.deny_consent(consent.id)
    assert denied.status == ConsentStatus.DENIED


def test_fetch_before_approval_raises(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    with pytest.raises(ValueError):
        aa_client.fetch_fi_data(consent.id)


def test_fetch_after_approval_generates_account_and_statement(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    aa_client.approve_consent(consent.id)

    account, statement = aa_client.fetch_fi_data(consent.id)

    assert account.source == "aa_pull"
    assert account.bank_name == "HDFC Bank"
    assert account.customer_id == "cust_1"
    assert statement.account_id == account.id
    assert len(statement.transactions) > 0
    assert all(t.account_id == account.id for t in statement.transactions)

    refetched = aa_client.get_consent(consent.id)
    assert refetched.data_fetched is True


def test_fetch_is_idempotent_and_deterministic(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    aa_client.approve_consent(consent.id)

    account_a, statement_a = aa_client.fetch_fi_data(consent.id)
    account_b, statement_b = aa_client.fetch_fi_data(consent.id)

    assert account_a.id == account_b.id
    assert [t.amount for t in statement_a.transactions] == [t.amount for t in statement_b.transactions]


def test_get_fetched_data_before_fetch_raises(aa_client):
    consent = aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    aa_client.approve_consent(consent.id)
    with pytest.raises(KeyError):
        aa_client.get_fetched_data(consent.id)


def test_list_consents_for_customer_filters_by_external_ref(aa_client):
    aa_client.create_consent_request("cust_1", "demo-001", "HDFC-FIP", "Loan underwriting")
    aa_client.create_consent_request("cust_2", "demo-002", "SBI-FIP", "Loan underwriting")

    consents = aa_client.list_consents_for_customer("demo-001")
    assert len(consents) == 1
    assert consents[0].external_ref == "demo-001"


def test_unknown_consent_id_raises_key_error(aa_client):
    with pytest.raises(KeyError):
        aa_client.get_consent("does-not-exist")
