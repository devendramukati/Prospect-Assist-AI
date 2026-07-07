import dataclasses
from functools import lru_cache
from pathlib import Path

import yaml

from app.models.domain import Transaction

DEFAULT_RULES_PATH = Path(__file__).parent / "rules" / "keywords.yaml"
UNCATEGORIZED = "uncategorized"


@dataclasses.dataclass(frozen=True)
class CategoryRule:
    pattern: str
    category: str
    subcategory: str | None
    direction: str | None
    confidence: float


@lru_cache(maxsize=4)
def _load_rules(rules_path: str = str(DEFAULT_RULES_PATH)) -> tuple[CategoryRule, ...]:
    raw = yaml.safe_load(Path(rules_path).read_text())
    return tuple(
        CategoryRule(
            pattern=r["pattern"],
            category=r["category"],
            subcategory=r.get("subcategory"),
            direction=r.get("direction"),
            confidence=r.get("confidence", 0.8),
        )
        for r in raw["rules"]
    )


def categorize_transaction(txn: Transaction, rules: tuple[CategoryRule, ...] | None = None) -> Transaction:
    rules = rules if rules is not None else _load_rules()
    description = txn.description_raw.upper()

    for rule in rules:
        if rule.direction and rule.direction != txn.direction:
            continue
        if rule.pattern.upper() in description:
            return txn.model_copy(
                update={
                    "category": rule.category,
                    "subcategory": rule.subcategory,
                    "confidence_score": rule.confidence,
                }
            )

    if txn.direction == "credit":
        return txn.model_copy(update={"category": "income", "subcategory": "other_credit", "confidence_score": 0.3})

    return txn.model_copy(update={"category": UNCATEGORIZED, "subcategory": None, "confidence_score": 0.0})


def categorize_transactions(transactions: list[Transaction]) -> list[Transaction]:
    rules = _load_rules()
    return [categorize_transaction(t, rules) for t in transactions]
