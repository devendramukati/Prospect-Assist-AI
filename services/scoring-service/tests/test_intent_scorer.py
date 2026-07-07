from app.models.domain import ApplicationEvent
from app.scoring_engine.intent_scorer import compute_intent_score


def _event(id_: str, event_type: str, ts: str = "2025-07-01T00:00:00") -> ApplicationEvent:
    return ApplicationEvent(id=id_, customer_id="c1", event_type=event_type, event_ts=ts)


def test_no_events_yields_zero_intent():
    result = compute_intent_score([])
    assert result["intent_score"] == 0.0
    assert result["max_stage"] is None


def test_disbursed_yields_max_intent():
    events = [_event("e1", "viewed_offer"), _event("e2", "started_application"), _event("e3", "disbursed")]
    result = compute_intent_score(events)
    assert result["max_stage"] == "disbursed"
    assert result["intent_score"] == 1.0


def test_repeated_viewed_offer_without_progress_is_penalized():
    events = [_event(f"e{i}", "viewed_offer") for i in range(4)]
    result = compute_intent_score(events)
    assert result["max_stage"] == "viewed_offer"
    assert result["viewed_offer_count"] == 4
    # base viewed_offer score (0.2) halved by the window-shopper penalty
    assert result["intent_score"] == 0.1


def test_single_viewed_offer_not_penalized():
    events = [_event("e1", "viewed_offer")]
    result = compute_intent_score(events)
    assert result["intent_score"] == 0.2


def test_submitted_documents_scores_below_disbursed_above_started():
    events = [_event("e1", "started_application"), _event("e2", "submitted_documents")]
    result = compute_intent_score(events)
    assert result["max_stage"] == "submitted_documents"
    assert 0.5 < result["intent_score"] < 1.0
