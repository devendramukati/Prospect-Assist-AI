import json
from pathlib import Path

import pytest


@pytest.fixture
def synthetic_data_dir(tmp_path: Path) -> Path:
    """A hand-built synthetic customer directory matching the file layout
    produced by packages/synthetic-data-generator's CLI, so scoring-service
    tests don't depend on that sibling package's internals — only on the
    file-format contract between them.
    """
    customer_dir = tmp_path / "customers" / "demo-001"
    (customer_dir / "statements").mkdir(parents=True)

    (customer_dir / "profile.json").write_text(
        json.dumps(
            {
                "id": "cust_demo001",
                "external_ref": "demo-001",
                "employment_type": "salaried",
                "archetype": "salaried_disciplined",
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        )
    )
    (customer_dir / "accounts.json").write_text(
        json.dumps(
            [
                {
                    "id": "acct_demo001",
                    "customer_id": "cust_demo001",
                    "bank_name": "HDFC Bank",
                    "masked_account_number": "XXXXXXXX1234",
                    "source": "upload",
                }
            ]
        )
    )
    (customer_dir / "application_events.json").write_text(
        json.dumps(
            [
                {
                    "id": "evt_1",
                    "customer_id": "cust_demo001",
                    "event_type": "viewed_offer",
                    "event_ts": "2025-07-01T00:00:00",
                    "metadata": {"loan_product": "personal_loan"},
                }
            ]
        )
    )

    transactions = []
    for month, amount in [("01", 75000.0), ("02", 75500.0), ("03", 74800.0)]:
        transactions.append(
            {
                "id": f"txn_salary_{month}", "account_id": "acct_demo001", "txn_date": f"2025-{month}-01",
                "description_raw": "NEFT-SALARY-EMPLOYER PVT LTD", "amount": amount,
                "direction": "credit", "channel": "NEFT",
            }
        )
        transactions.append(
            {
                "id": f"txn_emi_{month}", "account_id": "acct_demo001", "txn_date": f"2025-{month}-05",
                "description_raw": "ACH DEBIT-HOME LOAN EMI", "amount": 11000.0,
                "direction": "debit", "channel": "ACH",
            }
        )
    transactions.append(
        {
            "id": "txn_grocery_1", "account_id": "acct_demo001", "txn_date": "2025-01-10",
            "description_raw": "BIGBAZAAR SUPERMART", "amount": 3200.0,
            "direction": "debit", "channel": "POS",
        }
    )

    (customer_dir / "statements" / "acct_demo001.json").write_text(
        json.dumps(
            {
                "account_id": "acct_demo001",
                "period_start": "2025-01-01",
                "period_end": "2025-03-01",
                "transactions": transactions,
            }
        )
    )

    return tmp_path
