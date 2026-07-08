import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations.account_aggregator.mock_client import MockAAClient, get_aa_client
from app.main import app


@pytest.fixture
def client_with_fresh_aa(synthetic_data_dir, monkeypatch):
    """A TestClient wired to a brand-new MockAAClient per test, so consent
    state created in one test can't leak into another via the module-level
    singleton the app uses in production.
    """
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))
    fresh_client = MockAAClient()
    app.dependency_overrides[get_aa_client] = lambda: fresh_client
    yield TestClient(app), fresh_client
    app.dependency_overrides.pop(get_aa_client, None)


def test_list_fips(client_with_fresh_aa):
    client, _ = client_with_fresh_aa
    response = client.get("/consents/fips")
    assert response.status_code == 200
    assert len(response.json()["fips"]) >= 2


def test_full_consent_lifecycle(client_with_fresh_aa):
    client, _ = client_with_fresh_aa

    response = client.post("/consents/demo-001/request", json={"fip_id": "HDFC-FIP"})
    assert response.status_code == 200
    consent = response.json()
    assert consent["status"] == "pending"
    assert consent["data_range_from"] == "2025-01-01"
    assert consent["data_range_to"] == "2025-03-01"
    consent_id = consent["id"]

    response = client.post(f"/consents/{consent_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    response = client.post(f"/consents/{consent_id}/fetch")
    assert response.status_code == 200
    data = response.json()
    assert data["account"]["source"] == "aa_pull"
    assert len(data["statement"]["transactions"]) > 0

    response = client.get("/consents/demo-001")
    assert response.status_code == 200
    assert len(response.json()["consents"]) == 1


def test_request_consent_404_for_unknown_customer(client_with_fresh_aa):
    client, _ = client_with_fresh_aa
    response = client.post("/consents/does-not-exist/request", json={"fip_id": "HDFC-FIP"})
    assert response.status_code == 404


def test_request_consent_422_for_unknown_fip(client_with_fresh_aa):
    client, _ = client_with_fresh_aa
    response = client.post("/consents/demo-001/request", json={"fip_id": "UNKNOWN"})
    assert response.status_code == 422


def test_fetch_before_approval_returns_409(client_with_fresh_aa):
    client, _ = client_with_fresh_aa
    response = client.post("/consents/demo-001/request", json={"fip_id": "HDFC-FIP"})
    consent_id = response.json()["id"]

    response = client.post(f"/consents/{consent_id}/fetch")
    assert response.status_code == 409


def test_approve_unknown_consent_404(client_with_fresh_aa):
    client, _ = client_with_fresh_aa
    response = client.post("/consents/does-not-exist-id/approve")
    assert response.status_code == 404


def test_deny_consent(client_with_fresh_aa):
    client, _ = client_with_fresh_aa
    response = client.post("/consents/demo-001/request", json={"fip_id": "HDFC-FIP"})
    consent_id = response.json()["id"]

    response = client.post(f"/consents/{consent_id}/deny")
    assert response.status_code == 200
    assert response.json()["status"] == "denied"


def test_capacity_assessment_reflects_fetched_aa_account(client_with_fresh_aa):
    client, _ = client_with_fresh_aa

    before = client.get("/pipeline/demo-001/capacity-assessment").json()
    income_before = before["income"]["monthly_income_estimate"]

    response = client.post("/consents/demo-001/request", json={"fip_id": "HDFC-FIP"})
    consent_id = response.json()["id"]
    client.post(f"/consents/{consent_id}/approve")
    client.post(f"/consents/{consent_id}/fetch")

    after = client.get("/pipeline/demo-001/capacity-assessment").json()
    income_after = after["income"]["monthly_income_estimate"]

    assert income_after > income_before


def test_categorized_transactions_includes_linked_account_after_fetch(client_with_fresh_aa):
    client, _ = client_with_fresh_aa

    before = client.get("/pipeline/demo-001/categorized-transactions").json()
    assert len(before["statements"]) == 1

    response = client.post("/consents/demo-001/request", json={"fip_id": "SBI-FIP"})
    consent_id = response.json()["id"]
    client.post(f"/consents/{consent_id}/approve")
    client.post(f"/consents/{consent_id}/fetch")

    after = client.get("/pipeline/demo-001/categorized-transactions").json()
    assert len(after["statements"]) == 2
