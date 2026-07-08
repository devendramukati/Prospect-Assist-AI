"""End-to-end CI gate: runs the real synthetic-data-generator CLI, launches
the real scoring-service, and asserts each archetype lands in the tier the
stakeholder's narrative requires — this is a regression guard against
either package silently drifting apart, since Phases 1-4's hand-crafted
unit tests can't catch a contract break between them.
"""

from collections import defaultdict

from http_helpers import get_json

from conftest import PER_ARCHETYPE

# gig_worker's exact tier is naturally sensitive to RNG (its income/discipline
# signals are closer to threshold boundaries by archetype design), so it's
# allowed either qualifying tier — but never Interested/Not Qualified, which
# would mean the intent or discipline gate misfired for a customer who did
# progress through the funnel cleanly.
EXPECTED_TIERS = {
    "salaried_disciplined": {"Serious"},
    "strong_capacity_interested": {"Serious"},
    "multi_account_customer": {"Serious"},
    "salaried_spend_day1": {"Quality"},
    "window_shopper": {"Interested"},
    "business_owner_upi_heavy": {"Quality"},
    "gig_worker": {"Quality", "Serious"},
}

EXPECTED_CAPPED_BY = {
    "salaried_spend_day1": "discipline_gate",
    "window_shopper": "intent_gate",
}


def _group_by_archetype(leads: list[dict]) -> dict[str, list[dict]]:
    by_archetype: dict[str, list[dict]] = defaultdict(list)
    for lead in leads:
        archetype = lead["external_ref"].rsplit("-", 1)[0]
        by_archetype[archetype].append(lead)
    return by_archetype


def test_leads_endpoint_returns_every_archetype(smoke_backend_url):
    data = get_json(f"{smoke_backend_url}/leads")
    assert data["count"] == PER_ARCHETYPE * len(EXPECTED_TIERS)

    by_archetype = _group_by_archetype(data["leads"])
    assert set(by_archetype.keys()) == set(EXPECTED_TIERS.keys())


def test_each_archetype_lands_in_its_expected_tier(smoke_backend_url):
    leads = get_json(f"{smoke_backend_url}/leads")["leads"]
    by_archetype = _group_by_archetype(leads)

    for archetype, expected_tiers in EXPECTED_TIERS.items():
        actual_tiers = {lead["tier"] for lead in by_archetype[archetype]}
        assert actual_tiers <= expected_tiers, (
            f"{archetype}: expected tier(s) within {expected_tiers}, got {actual_tiers}"
        )


def test_discipline_and_intent_gates_fire_for_their_archetypes(smoke_backend_url):
    leads = get_json(f"{smoke_backend_url}/leads")["leads"]
    by_archetype = _group_by_archetype(leads)

    for archetype, expected_capped_by in EXPECTED_CAPPED_BY.items():
        capped_by_values = {lead["capped_by"] for lead in by_archetype[archetype]}
        assert capped_by_values == {expected_capped_by}, (
            f"{archetype}: expected capped_by={expected_capped_by!r} for every lead, got {capped_by_values}"
        )


def test_no_transaction_goes_uncategorized(smoke_backend_url):
    leads = get_json(f"{smoke_backend_url}/leads")["leads"]
    for lead in leads:
        detail = get_json(f"{smoke_backend_url}/pipeline/{lead['external_ref']}/categorized-transactions")
        for statement in detail["statements"]:
            uncategorized = [t for t in statement["transactions"] if t["category"] == "uncategorized"]
            assert not uncategorized, f"{lead['external_ref']} has uncategorized transactions: {uncategorized}"
