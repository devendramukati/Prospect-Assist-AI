import random
from datetime import datetime, timedelta

from .archetypes import ArchetypeConfig
from .models import ApplicationEvent

FUNNEL_STAGES = ["viewed_offer", "started_application", "consented_statement_pull", "submitted_documents", "disbursed"]


def _event_id(rng: random.Random) -> str:
    return f"evt_{rng.getrandbits(48):012x}"


def generate_funnel_events(
    cfg: ArchetypeConfig,
    customer_id: str,
    application_start: datetime,
    rng: random.Random,
) -> list[ApplicationEvent]:
    """Intent signal derived purely from loan-origination funnel events (no clickstream needed).

    A window-shopper archetype sets funnel.max_stage="viewed_offer" and a high
    product_views count, so it repeatedly checks eligibility but never
    proceeds — the exact behaviour the scoring engine (Phase 4) needs to
    down-rank despite any income/capacity signal.
    """
    events: list[ApplicationEvent] = []
    max_index = FUNNEL_STAGES.index(cfg.funnel.max_stage)
    current_ts = application_start

    for _ in range(cfg.funnel.product_views):
        events.append(
            ApplicationEvent(
                id=_event_id(rng), customer_id=customer_id,
                event_type="viewed_offer", event_ts=current_ts.isoformat(),
                metadata={"loan_product": cfg.funnel.loan_product},
            )
        )
        current_ts += timedelta(hours=rng.randint(4, 96))

    for stage in FUNNEL_STAGES[1 : max_index + 1]:
        events.append(
            ApplicationEvent(
                id=_event_id(rng), customer_id=customer_id,
                event_type=stage, event_ts=current_ts.isoformat(),
                metadata={"loan_product": cfg.funnel.loan_product, "requested_amount": cfg.funnel.requested_amount},
            )
        )
        current_ts += timedelta(hours=rng.randint(6, 72))

    return events
