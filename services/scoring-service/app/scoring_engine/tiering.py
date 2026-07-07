TIER_SERIOUS = "Serious"
TIER_QUALITY = "Quality"
TIER_INTERESTED = "Interested"
TIER_NOT_QUALIFIED = "Not Qualified"

# A customer who never progressed past viewing an offer can't be called
# "Serious" or "Quality" no matter how strong their finances look — this is
# the concrete fix for window-shopper leads consuming relationship-manager
# effort without genuine intent.
INTENT_GATE_STAGES = {"started_application", "consented_statement_pull", "submitted_documents", "disbursed"}

# A pronounced day-1 spend-everything pattern or an actual bounced payment
# is a delinquency-risk signal that should cap the tier even when income and
# funnel progression look fine — the stakeholder's explicit "spends the
# salary on day 1" concern.
DISCIPLINE_RED_FLAG_DAY1_THRESHOLD = 0.5


def assign_tier(
    composite_score: float,
    max_stage: str | None,
    day1_spend_velocity_pct: float,
    bounce_flag: bool,
) -> dict:
    if max_stage not in INTENT_GATE_STAGES:
        tier = TIER_INTERESTED if composite_score >= 0.35 else TIER_NOT_QUALIFIED
        return {
            "tier": tier,
            "capped_by": "intent_gate",
            "reasons": ["Never progressed past viewing an offer — capped below Quality/Serious regardless of finances"],
        }

    if bounce_flag or day1_spend_velocity_pct >= DISCIPLINE_RED_FLAG_DAY1_THRESHOLD:
        tier = TIER_QUALITY if composite_score >= 0.55 else TIER_INTERESTED
        return {
            "tier": tier,
            "capped_by": "discipline_gate",
            "reasons": ["Discipline red flag (bounced payment or high day-1 spend velocity) — capped below Serious"],
        }

    if composite_score >= 0.75:
        tier = TIER_SERIOUS
    elif composite_score >= 0.55:
        tier = TIER_QUALITY
    elif composite_score >= 0.35:
        tier = TIER_INTERESTED
    else:
        tier = TIER_NOT_QUALIFIED

    return {"tier": tier, "capped_by": None, "reasons": []}
