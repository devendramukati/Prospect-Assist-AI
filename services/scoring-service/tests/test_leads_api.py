from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_list_leads_includes_fixture_customer(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/leads")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 1
    lead = data["leads"][0]
    assert lead["external_ref"] == "demo-001"
    assert lead["employment_type"] == "salaried"
    assert lead["tier"] in {"Serious", "Quality", "Interested", "Not Qualified"}
    # fixture only has a single viewed_offer event — never started an application
    assert lead["capped_by"] == "intent_gate"
    assert lead["max_stage"] == "viewed_offer"
    assert lead["reached_disbursed"] is False
    assert lead["discipline_flagged"] is False


def test_explain_lead_returns_full_breakdown(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/leads/demo-001/explain")
    assert response.status_code == 200

    data = response.json()
    assert data["customer"]["external_ref"] == "demo-001"
    assert "assessment" in data and "income" in data["assessment"]
    assert data["score"]["capped_by"] == "intent_gate"
    factor_names = {f["factor"] for f in data["score"]["explanation"]["factors"]}
    assert factor_names == {"intent", "capacity", "discipline"}


def test_explain_lead_404_for_unknown_customer(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/leads/does-not-exist/explain")
    assert response.status_code == 404


def test_underwriting_report_shape(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/leads/demo-001/underwriting-report")
    assert response.status_code == 200

    data = response.json()
    assert data["customer"]["external_ref"] == "demo-001"
    assert data["income_summary"]["method"] == "fixed_salary"
    assert data["income_summary"]["confidence_band"] is None
    assert "personal_loan" in data["affordability"]["by_product"]
    assert data["lead_tier"] in {"Serious", "Quality", "Interested", "Not Qualified"}
    assert isinstance(data["risk_flags"], list)


def test_underwriting_report_404_for_unknown_customer(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/leads/does-not-exist/underwriting-report")
    assert response.status_code == 404
