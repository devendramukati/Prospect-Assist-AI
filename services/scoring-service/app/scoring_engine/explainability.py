def build_explanation(
    intent: dict,
    capacity_score: float,
    discipline_score: float,
    weights: dict,
    composite_score: float,
    tiering_result: dict,
) -> dict:
    """A factor-weighted breakdown of the score, persisted alongside every
    scoring run — this is what lets a relationship manager (and, for
    compliance, an auditor) see *why* a lead landed in a given tier, rather
    than trusting an opaque number.
    """
    return {
        "composite_score": composite_score,
        "tier": tiering_result["tier"],
        "capped_by": tiering_result["capped_by"],
        "gate_reasons": tiering_result["reasons"],
        "factors": [
            {
                "factor": "intent",
                "score": intent["intent_score"],
                "weight": weights["intent"],
                "contribution": round(intent["intent_score"] * weights["intent"], 4),
                "detail": f"Reached {intent['max_stage']!s} ({intent['viewed_offer_count']} offer view(s))",
            },
            {
                "factor": "capacity",
                "score": capacity_score,
                "weight": weights["capacity"],
                "contribution": round(capacity_score * weights["capacity"], 4),
            },
            {
                "factor": "discipline",
                "score": discipline_score,
                "weight": weights["discipline"],
                "contribution": round(discipline_score * weights["discipline"], 4),
            },
        ],
    }
