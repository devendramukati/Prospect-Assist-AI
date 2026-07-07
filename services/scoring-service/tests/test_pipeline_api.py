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
