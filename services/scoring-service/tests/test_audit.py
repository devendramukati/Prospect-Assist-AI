import json
import logging

from app.core.audit import record_audit_event


def test_record_audit_event_returns_structured_event():
    event = record_audit_event("consent", "consent_123", "approved", actor="loan_officer_1", metadata={"foo": "bar"})
    assert event["entity_type"] == "consent"
    assert event["entity_id"] == "consent_123"
    assert event["action"] == "approved"
    assert event["actor"] == "loan_officer_1"
    assert event["metadata"] == {"foo": "bar"}
    assert "timestamp" in event


def test_record_audit_event_defaults_actor_to_system():
    event = record_audit_event("consent", "consent_123", "requested")
    assert event["actor"] == "system"
    assert event["metadata"] == {}


def test_record_audit_event_logs_valid_json(caplog):
    with caplog.at_level(logging.INFO, logger="audit"):
        record_audit_event("consent", "consent_abc", "fetched", metadata={"linked_account_id": "acct_1"})

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["entity_id"] == "consent_abc"
    assert logged["action"] == "fetched"
