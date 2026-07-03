import random
import statistics
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from generators.archetypes import load_archetypes
from generators.funnel_events import generate_funnel_events
from generators.models import Statement
from generators.statements import build_accounts_and_statements

CONFIG_DIR = Path(__file__).parent.parent / "config" / "archetypes"
PERIOD_START = date(2025, 1, 1)
PERIOD_MONTHS = 6


def _generate(name: str, index: int = 0):
    archetypes = load_archetypes(CONFIG_DIR)
    cfg = archetypes[name]
    rng = random.Random(f"test-{name}-{index}")
    customer_id = "test-customer"
    accounts, statements = build_accounts_and_statements(cfg, customer_id, PERIOD_START, PERIOD_MONTHS, rng)
    events = generate_funnel_events(cfg, customer_id, datetime(2025, 7, 1), rng)
    return cfg, accounts, statements, events


def _credit_transactions(statements: list[Statement]):
    return [t for stmt in statements for t in stmt.transactions if t.direction == "credit"]


def _monthly_income_totals(statements: list[Statement]) -> list[float]:
    totals: dict[str, float] = {}
    for stmt in statements:
        for t in stmt.transactions:
            if t.direction == "credit":
                month = t.txn_date[:7]
                totals[month] = totals.get(month, 0) + t.amount
    return list(totals.values())


def _day1_spend_ratio(statements: list[Statement]) -> float:
    """Rough replica of the discipline-engine's day-1 velocity signal.

    This exists only to prove the generator produces distinguishable
    archetypes; the production metric lives in Phase 3's discipline_engine.
    """
    all_txns = [t for stmt in statements for t in stmt.transactions]
    by_month = defaultdict(list)
    for t in all_txns:
        by_month[t.txn_date[:7]].append(t)

    ratios = []
    for month_txns in by_month.values():
        credits = sorted((t for t in month_txns if t.direction == "credit"), key=lambda t: t.amount, reverse=True)[:3]
        total_credit = sum(t.amount for t in credits)
        if total_credit == 0:
            continue
        credit_dates = [date.fromisoformat(c.txn_date) for c in credits]
        day1_total = sum(
            t.amount
            for t in month_txns
            if t.direction == "debit"
            and any(0 <= (date.fromisoformat(t.txn_date) - cd).days <= 2 for cd in credit_dates)
        )
        ratios.append(day1_total / total_credit)
    return statistics.mean(ratios) if ratios else 0.0


def test_all_archetype_configs_load_without_error():
    archetypes = load_archetypes(CONFIG_DIR)
    expected = {
        "salaried_disciplined", "salaried_spend_day1", "gig_worker",
        "business_owner_upi_heavy", "window_shopper", "strong_capacity_interested",
        "multi_account_customer",
    }
    assert expected <= set(archetypes.keys())


def test_salaried_disciplined_has_low_day1_velocity():
    _, _, statements, _ = _generate("salaried_disciplined")
    assert _day1_spend_ratio(statements) < 0.3


def test_salaried_spend_day1_has_high_day1_velocity():
    _, _, statements, _ = _generate("salaried_spend_day1")
    assert _day1_spend_ratio(statements) > 0.6


def test_gig_worker_income_is_more_volatile_than_salaried():
    _, _, salaried_statements, _ = _generate("salaried_disciplined")
    _, _, gig_statements, _ = _generate("gig_worker")
    salaried_totals = _monthly_income_totals(salaried_statements)
    gig_totals = _monthly_income_totals(gig_statements)
    salaried_cov = statistics.pstdev(salaried_totals) / statistics.mean(salaried_totals)
    gig_cov = statistics.pstdev(gig_totals) / statistics.mean(gig_totals)
    assert gig_cov > salaried_cov


def test_business_owner_has_many_small_upi_credits():
    _, _, statements, _ = _generate("business_owner_upi_heavy")
    credits = _credit_transactions(statements)
    # ~60 UPI credits/month * 6 months, far above a salaried/gig customer's credit count
    assert len(credits) > 100


def test_window_shopper_stalls_early_in_funnel():
    _, _, _, events = _generate("window_shopper")
    stages_reached = {e.event_type for e in events}
    assert "submitted_documents" not in stages_reached
    assert "disbursed" not in stages_reached
    assert stages_reached <= {"viewed_offer", "started_application"}


def test_strong_capacity_interested_reaches_disbursed():
    _, _, _, events = _generate("strong_capacity_interested")
    stages_reached = {e.event_type for e in events}
    assert "disbursed" in stages_reached


def test_multi_account_customer_has_two_accounts_from_different_sources():
    _, accounts, _, _ = _generate("multi_account_customer")
    assert len(accounts) == 2
    assert {a.source for a in accounts} == {"upload", "aa_pull"}


def test_generation_is_deterministic_for_a_given_seed():
    _, _, statements_a, _ = _generate("gig_worker", index=7)
    _, _, statements_b, _ = _generate("gig_worker", index=7)
    amounts_a = [t.amount for stmt in statements_a for t in stmt.transactions]
    amounts_b = [t.amount for stmt in statements_b for t in stmt.transactions]
    assert amounts_a == amounts_b
