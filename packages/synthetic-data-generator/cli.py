import argparse
import dataclasses
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from generators.archetypes import ArchetypeConfig, load_archetypes
from generators.funnel_events import generate_funnel_events
from generators.models import ApplicationEvent, BankAccount, Customer, Statement
from generators.statements import build_accounts_and_statements

DEFAULT_CONFIG_DIR = Path(__file__).parent / "config" / "archetypes"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "data"
DEFAULT_PERIOD_MONTHS = 6


def _to_json(obj):
    return dataclasses.asdict(obj)


def generate_customer(
    archetype_name: str,
    cfg: ArchetypeConfig,
    index: int,
    seed: str,
    period_start: date,
    period_months: int,
) -> tuple[Customer, list[BankAccount], list[Statement], list[ApplicationEvent]]:
    rng = random.Random(f"{seed}-{archetype_name}-{index}")
    customer_id = f"cust_{rng.getrandbits(48):012x}"
    external_ref = f"{archetype_name}-{index:03d}"
    customer = Customer(
        id=customer_id, external_ref=external_ref, employment_type=cfg.employment_type,
        archetype=archetype_name, created_at=datetime.now(timezone.utc).isoformat(),
    )
    accounts, statements = build_accounts_and_statements(cfg, customer_id, period_start, period_months, rng)
    application_start = (
        datetime.combine(period_start, datetime.min.time())
        + timedelta(days=period_months * 30 + rng.randint(0, 5))
    )
    events = generate_funnel_events(cfg, customer_id, application_start, rng)
    return customer, accounts, statements, events


def write_customer(
    output_dir: Path,
    customer: Customer,
    accounts: list[BankAccount],
    statements: list[Statement],
    events: list[ApplicationEvent],
) -> None:
    customer_dir = output_dir / "customers" / customer.external_ref
    customer_dir.mkdir(parents=True, exist_ok=True)
    (customer_dir / "profile.json").write_text(json.dumps(_to_json(customer), indent=2))
    (customer_dir / "accounts.json").write_text(json.dumps([_to_json(a) for a in accounts], indent=2))

    statements_dir = customer_dir / "statements"
    statements_dir.mkdir(exist_ok=True)
    for stmt in statements:
        (statements_dir / f"{stmt.account_id}.json").write_text(json.dumps(_to_json(stmt), indent=2))

    (customer_dir / "application_events.json").write_text(json.dumps([_to_json(e) for e in events], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic bank-statement/lead data for Prospect-Assist-AI")
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-archetype", type=int, default=30, help="customers to generate per archetype")
    parser.add_argument("--period-months", type=int, default=DEFAULT_PERIOD_MONTHS)
    parser.add_argument("--seed", type=str, default="prospect-assist-mvp")
    parser.add_argument("--start-date", type=str, default=None, help="YYYY-MM-DD, defaults to N months before today")
    args = parser.parse_args()

    period_start = (
        date.fromisoformat(args.start_date) if args.start_date
        else date.today().replace(day=1) - timedelta(days=args.period_months * 30)
    ).replace(day=1)

    archetypes = load_archetypes(args.config_dir)
    if not archetypes:
        raise SystemExit(f"No archetype configs found in {args.config_dir}")

    manifest = []
    for archetype_name, cfg in archetypes.items():
        for i in range(args.per_archetype):
            customer, accounts, statements, events = generate_customer(
                archetype_name, cfg, i, args.seed, period_start, args.period_months
            )
            write_customer(args.output_dir, customer, accounts, statements, events)
            manifest.append(
                {
                    "external_ref": customer.external_ref,
                    "archetype": archetype_name,
                    "employment_type": cfg.employment_type,
                    "customer_id": customer.id,
                }
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Generated {len(manifest)} synthetic customers across {len(archetypes)} archetypes into {args.output_dir}")


if __name__ == "__main__":
    main()
