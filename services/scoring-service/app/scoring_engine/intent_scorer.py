from app.models.domain import ApplicationEvent

STAGE_SCORES = {
    "viewed_offer": 0.2,
    "started_application": 0.5,
    "consented_statement_pull": 0.7,
    "submitted_documents": 0.85,
    "disbursed": 1.0,
}

# Repeatedly viewing an offer without ever starting an application is the
# concrete "window shopper" pattern the stakeholder called out — someone
# checking eligibility again and again but never actually committing. More
# than this many repeat views with no progression discounts the score.
WINDOW_SHOPPER_VIEW_THRESHOLD = 2
WINDOW_SHOPPER_PENALTY = 0.5


def compute_intent_score(events: list[ApplicationEvent]) -> dict:
    if not events:
        return {"intent_score": 0.0, "max_stage": None, "viewed_offer_count": 0}

    stages_reached = {e.event_type for e in events}
    max_stage = max(stages_reached, key=lambda s: STAGE_SCORES.get(s, 0.0))
    intent_score = STAGE_SCORES.get(max_stage, 0.0)

    viewed_offer_count = sum(1 for e in events if e.event_type == "viewed_offer")
    if max_stage == "viewed_offer" and viewed_offer_count > WINDOW_SHOPPER_VIEW_THRESHOLD:
        intent_score *= WINDOW_SHOPPER_PENALTY

    return {
        "intent_score": round(intent_score, 4),
        "max_stage": max_stage,
        "viewed_offer_count": viewed_offer_count,
    }
