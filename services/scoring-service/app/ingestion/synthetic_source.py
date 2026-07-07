import json
from pathlib import Path

from app.ingestion.base import IngestionSource
from app.models.domain import ApplicationEvent, BankAccount, Customer, CustomerBundle, Statement, Transaction


class SyntheticFileIngestionSource(IngestionSource):
    """Reads the file layout produced by packages/synthetic-data-generator:

        data/customers/<external_ref>/profile.json
        data/customers/<external_ref>/accounts.json
        data/customers/<external_ref>/application_events.json
        data/customers/<external_ref>/statements/<account_id>.json

    Used for local dev/demo since no real bank data is available for the MVP.
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def list_external_refs(self) -> list[str]:
        """Lists every customer this synthetic source can serve. Not part of
        the IngestionSource interface (a real PDF upload or AA pull is
        inherently per-customer) — used only by the /leads listing endpoint
        for this MVP demo; a real deployment would query the DB instead.
        """
        customers_dir = self.data_dir / "customers"
        if not customers_dir.is_dir():
            return []
        return sorted(p.name for p in customers_dir.iterdir() if p.is_dir())

    def load(self, external_ref: str) -> CustomerBundle:
        customer_dir = self.data_dir / "customers" / external_ref
        if not customer_dir.is_dir():
            raise FileNotFoundError(f"No synthetic customer data found for {external_ref!r} in {self.data_dir}")

        profile = json.loads((customer_dir / "profile.json").read_text())
        customer = Customer(
            id=profile["id"],
            external_ref=profile["external_ref"],
            employment_type=profile["employment_type"],
            created_at=profile["created_at"],
        )

        accounts = [BankAccount(**a) for a in json.loads((customer_dir / "accounts.json").read_text())]

        statements = []
        for path in sorted((customer_dir / "statements").glob("*.json")):
            raw = json.loads(path.read_text())
            statements.append(
                Statement(
                    account_id=raw["account_id"],
                    period_start=raw["period_start"],
                    period_end=raw["period_end"],
                    transactions=[Transaction(**t) for t in raw["transactions"]],
                )
            )

        events = [ApplicationEvent(**e) for e in json.loads((customer_dir / "application_events.json").read_text())]

        return CustomerBundle(customer=customer, accounts=accounts, statements=statements, application_events=events)
