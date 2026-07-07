from app.scoring_engine.tiering import assign_tier


def test_intent_gate_caps_high_score_lead_that_never_started_application():
    result = assign_tier(composite_score=0.95, max_stage="viewed_offer", day1_spend_velocity_pct=0.0, bounce_flag=False)
    assert result["tier"] == "Interested"
    assert result["capped_by"] == "intent_gate"


def test_intent_gate_drops_to_not_qualified_below_threshold():
    result = assign_tier(composite_score=0.2, max_stage=None, day1_spend_velocity_pct=0.0, bounce_flag=False)
    assert result["tier"] == "Not Qualified"
    assert result["capped_by"] == "intent_gate"


def test_discipline_gate_caps_high_score_lead_with_high_day1_velocity():
    result = assign_tier(composite_score=0.9, max_stage="disbursed", day1_spend_velocity_pct=0.7, bounce_flag=False)
    assert result["tier"] == "Quality"
    assert result["capped_by"] == "discipline_gate"


def test_discipline_gate_caps_lead_with_bounced_payment():
    result = assign_tier(composite_score=0.9, max_stage="disbursed", day1_spend_velocity_pct=0.1, bounce_flag=True)
    assert result["tier"] == "Quality"
    assert result["capped_by"] == "discipline_gate"


def test_normal_thresholds_apply_when_no_gate_triggers():
    serious = assign_tier(composite_score=0.8, max_stage="disbursed", day1_spend_velocity_pct=0.1, bounce_flag=False)
    quality = assign_tier(composite_score=0.6, max_stage="disbursed", day1_spend_velocity_pct=0.1, bounce_flag=False)
    interested = assign_tier(composite_score=0.4, max_stage="disbursed", day1_spend_velocity_pct=0.1, bounce_flag=False)
    not_qualified = assign_tier(composite_score=0.1, max_stage="disbursed", day1_spend_velocity_pct=0.1, bounce_flag=False)

    assert serious["tier"] == "Serious" and serious["capped_by"] is None
    assert quality["tier"] == "Quality" and quality["capped_by"] is None
    assert interested["tier"] == "Interested" and interested["capped_by"] is None
    assert not_qualified["tier"] == "Not Qualified" and not_qualified["capped_by"] is None
