"""Regression tests locking in the expected tier for each MVP archetype's
defining characteristics (Phase 1's config descriptions), built as clean,
hand-computed representative inputs rather than the real generator's noisy
output — this tests that the tiering logic reflects the intended stakeholder
narrative deterministically, independent of RNG-driven statement data.
"""

from app.models.domain import ApplicationEvent
from app.scoring_engine.composite_scorer import compute_composite_score


def _events(stages: list[str], viewed_offer_count: int = 1) -> list[ApplicationEvent]:
    events = [
        ApplicationEvent(id=f"v{i}", customer_id="c1", event_type="viewed_offer", event_ts="2025-07-01T00:00:00")
        for i in range(viewed_offer_count)
    ]
    events += [
        ApplicationEvent(id=f"s{i}", customer_id="c1", event_type=stage, event_ts="2025-07-02T00:00:00")
        for i, stage in enumerate(stages)
    ]
    return events


def _assessment(
    monthly_income: float,
    income_stability: float,
    disposable_income: float,
    day1_pct: float,
    bounce_flag: bool = False,
    went_negative: bool = False,
    method: str = "fixed_salary",
    capacity_base_income: float | None = None,
) -> dict:
    return {
        "income": {
            "method": method,
            "monthly_income_estimate": monthly_income,
            "income_stability_score": income_stability,
            "sample_size": 6,
            "confidence_low": None,
            "confidence_high": None,
            "supporting_evidence": {},
        },
        "disposable_income": {"disposable_income": disposable_income, "foir_pct": 0.15},
        "capacity_base_income": capacity_base_income if capacity_base_income is not None else monthly_income,
        "discipline": {
            "day1_spend_velocity": {"day1_spend_velocity_pct": day1_pct, "months_observed": 6},
            "bounce": {"bounce_count": 1 if bounce_flag else 0, "bounce_flag": bounce_flag},
            "balance": {
                "minimum_running_balance": -100.0 if went_negative else 0.0,
                "low_balance_event_count": 0,
                "went_negative": went_negative,
            },
        },
    }


def test_strong_capacity_interested_lands_in_serious():
    assessment = _assessment(monthly_income=150000, income_stability=0.97, disposable_income=115000, day1_pct=0.05)
    events = _events(["started_application", "consented_statement_pull", "submitted_documents", "disbursed"])
    result = compute_composite_score(events, assessment)
    assert result["tier"] == "Serious"
    assert result["capped_by"] is None


def test_salaried_spend_day1_capped_below_serious_by_discipline_gate():
    # Otherwise strong income/intent, but day-1 spend velocity trips the gate.
    assessment = _assessment(monthly_income=80000, income_stability=0.95, disposable_income=68000, day1_pct=0.70)
    events = _events(["started_application", "consented_statement_pull", "submitted_documents"])
    result = compute_composite_score(events, assessment)
    assert result["tier"] == "Quality"
    assert result["capped_by"] == "discipline_gate"


def test_window_shopper_capped_below_quality_by_intent_gate():
    # Strong finances, but never actually starts an application.
    assessment = _assessment(monthly_income=60000, income_stability=0.94, disposable_income=44000, day1_pct=0.10)
    events = _events([], viewed_offer_count=4)
    result = compute_composite_score(events, assessment)
    assert result["tier"] == "Interested"
    assert result["capped_by"] == "intent_gate"


def test_weak_finances_and_no_application_lands_not_qualified():
    assessment = _assessment(monthly_income=20000, income_stability=0.3, disposable_income=2000, day1_pct=0.30)
    result = compute_composite_score([], assessment)
    assert result["tier"] == "Not Qualified"


def test_gig_worker_moderate_profile_lands_in_quality():
    assessment = _assessment(monthly_income=39000, income_stability=0.75, disposable_income=20000, day1_pct=0.35)
    events = _events(["started_application", "submitted_documents"], viewed_offer_count=2)
    result = compute_composite_score(events, assessment)
    assert result["tier"] == "Quality"
    assert result["capped_by"] is None


def test_business_owner_turnover_basis_lands_in_quality():
    # capacity_base_income (turnover) differs sharply from the margin-based
    # monthly_income_estimate — the scorer must use the turnover basis.
    assessment = _assessment(
        monthly_income=100000, income_stability=0.5, disposable_income=400000, day1_pct=0.0,
        method="turnover_margin", capacity_base_income=800000,
    )
    events = _events(["started_application", "consented_statement_pull"])
    result = compute_composite_score(events, assessment)
    assert result["tier"] == "Quality"


def test_multi_account_consolidated_income_lands_in_serious():
    assessment = _assessment(monthly_income=95000, income_stability=0.95, disposable_income=66500, day1_pct=0.10)
    events = _events(["started_application", "consented_statement_pull"])
    result = compute_composite_score(events, assessment)
    assert result["tier"] == "Serious"
    assert result["capped_by"] is None
