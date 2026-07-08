import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("audit")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def record_audit_event(
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str = "system",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Appends one structured, append-only audit event.

    This is a stand-in for the `audit_log` DB table (see
    infra/supabase/migrations/0002_consents_and_audit_log.sql) until real
    persistence is wired up — every consent-lifecycle action and
    underwriting-report generation is recorded here so there is a
    compliance trail even before the table is live. `actor` defaults to
    "system" because this MVP has no authenticated-user session yet; a real
    deployment would pass the logged-in loan officer's user ID here.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor": actor,
        "action": action,
        "metadata": metadata or {},
    }
    logger.info(json.dumps(event))
    return event
