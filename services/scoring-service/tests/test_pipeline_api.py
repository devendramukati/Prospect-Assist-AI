from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_categorized_transactions_endpoint(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/pipeline/demo-001/categorized-transactions")
    assert response.status_code == 200

    data = response.json()
    assert data["customer"]["external_ref"] == "demo-001"

    transactions = data["statements"][0]["transactions"]
    salary_txns = [t for t in transactions if t["subcategory"] == "salary"]
    emi_txns = [t for t in transactions if t["subcategory"] == "home_loan_emi"]
    grocery_txns = [t for t in transactions if t["subcategory"] == "groceries"]

    assert len(salary_txns) == 3
    assert all(t["is_recurring"] for t in salary_txns)
    assert len(emi_txns) == 3
    assert all(t["is_recurring"] for t in emi_txns)
    assert len(grocery_txns) == 1
    assert not grocery_txns[0]["is_recurring"]


def test_categorized_transactions_endpoint_404_for_unknown_customer(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/pipeline/does-not-exist/categorized-transactions")
    assert response.status_code == 404


def test_capacity_assessment_endpoint(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/pipeline/demo-001/capacity-assessment")
    assert response.status_code == 200

    data = response.json()
    assert data["customer"]["external_ref"] == "demo-001"
    assert data["income"]["method"] == "fixed_salary"
    assert 74800 <= data["income"]["monthly_income_estimate"] <= 75500
    assert data["expense_summary"]["compulsory_obligations"] == 11000.0
    assert data["disposable_income"]["disposable_income"] > 0
    assert set(data["affordability_by_product"].keys()) == {
        "personal_loan", "auto_loan", "home_loan", "mortgage_loan",
    }
    assert data["discipline"]["bounce"]["bounce_count"] == 0
    assert data["discipline"]["day1_spend_velocity"]["months_observed"] == 3


def test_capacity_assessment_endpoint_404_for_unknown_customer(synthetic_data_dir, monkeypatch):
    monkeypatch.setattr(settings, "synthetic_data_dir", str(synthetic_data_dir))

    response = client.get("/pipeline/does-not-exist/capacity-assessment")
    assert response.status_code == 404
