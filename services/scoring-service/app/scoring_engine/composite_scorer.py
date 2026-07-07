from functools import lru_cache
from pathlib import Path

import yaml

from app.models.domain import ApplicationEvent
from app.scoring_engine.explainability import build_explanation
from app.scoring_engine.intent_scorer import compute_intent_score
from app.scoring_engine.tiering import assign_tier

DEFAULT_WEIGHTS_PATH = Path(__file__).parent / "config" / "weights_v1.yaml"
SCORING_VERSION = "v1"


@lru_cache(maxsize=4)
def _load_weights(path: str = str(DEFAULT_WEIGHTS_PATH)) -> dict:
    return yaml.safe_load(Path(path).read_text())


def _capacity_score(assessment: dict) -> float:
    """0.6x weight on disposable-income headroom, 0.4x on income stability.
    Uses `capacity_base_income` (which matches whatever basis — net income
    or turnover — disposable_income was computed against) rather than
    `income.monthly_income_estimate` directly, since those two can be on
    different scales for a turnover-margin-method customer.
    """
    base_income = assessment.get("capacity_base_income", assessment["income"]["monthly_income_estimate"])
    disposable = assessment["disposable_income"]["disposable_income"]
    disposable_ratio = max(0.0, min(1.0, disposable / base_income)) if base_income > 0 else 0.0
    stability = assessment["income"]["income_stability_score"]
    return round(0.6 * disposable_ratio + 0.4 * stability, 4)


def _discipline_score(assessment: dict) -> float:
    discipline = assessment["discipline"]
    day1_pct = discipline["day1_spend_velocity"]["day1_spend_velocity_pct"]

    score = 1.0 - min(day1_pct, 1.0) * 0.5
    if discipline["bounce"]["bounce_flag"]:
        score -= 0.3
    if discipline["balance"]["went_negative"]:
        score -= 0.2

    return round(max(0.0, min(1.0, score)), 4)


def compute_composite_score(
    application_events: list[ApplicationEvent],
    capacity_assessment: dict,
    scoring_version: str = SCORING_VERSION,
) -> dict:
    weights = _load_weights()
    intent = compute_intent_score(application_events)
    capacity_score = _capacity_score(capacity_assessment)
    discipline_score = _discipline_score(capacity_assessment)

    composite_score = round(
        weights["intent"] * intent["intent_score"]
        + weights["capacity"] * capacity_score
        + weights["discipline"] * discipline_score,
        4,
    )

    discipline = capacity_assessment["discipline"]
    tiering_result = assign_tier(
        composite_score=composite_score,
        max_stage=intent["max_stage"],
        day1_spend_velocity_pct=discipline["day1_spend_velocity"]["day1_spend_velocity_pct"],
        bounce_flag=discipline["bounce"]["bounce_flag"],
    )

    explanation = build_explanation(intent, capacity_score, discipline_score, weights, composite_score, tiering_result)

    return {
        "scoring_version": scoring_version,
        "intent_score": intent["intent_score"],
        "capacity_score": capacity_score,
        "discipline_score": discipline_score,
        "composite_score": composite_score,
        "tier": tiering_result["tier"],
        "capped_by": tiering_result["capped_by"],
        "explanation": explanation,
    }
