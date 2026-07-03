import dataclasses
from pathlib import Path

import yaml


@dataclasses.dataclass
class IncomeConfig:
    type: str  # fixed_salary | irregular | business_turnover
    monthly_amount: float | None = None
    variance_pct: float = 0.0
    pay_day: int | None = None
    monthly_mean: float | None = None
    monthly_stddev_pct: float | None = None
    monthly_turnover: float | None = None
    turnover_variance_pct: float | None = None
    industry: str | None = None
    margin_band: list[float] | None = None
    txn_count_per_month: int | None = None


@dataclasses.dataclass
class ExpenseConfig:
    essential_needs_pct: float
    compulsory_obligations_pct: float
    discretionary_pct: float
    savings_investment_pct: float


@dataclasses.dataclass
class DisciplineConfig:
    day1_spend_velocity_pct: float
    bounce_event_probability: float = 0.0


@dataclasses.dataclass
class FunnelConfig:
    max_stage: str
    product_views: int
    loan_product: str
    requested_amount: float


@dataclasses.dataclass
class AccountsConfig:
    count: int = 1
    income_split: list[float] | None = None


@dataclasses.dataclass
class ArchetypeConfig:
    name: str
    employment_type: str
    income: IncomeConfig
    expenses: ExpenseConfig
    discipline: DisciplineConfig
    funnel: FunnelConfig
    accounts: AccountsConfig
    description: str = ""

    def __post_init__(self) -> None:
        total_pct = (
            self.expenses.essential_needs_pct
            + self.expenses.compulsory_obligations_pct
            + self.expenses.discretionary_pct
            + self.expenses.savings_investment_pct
        )
        if total_pct > 1.0 + 1e-6:
            raise ValueError(f"{self.name}: expense percentages sum to {total_pct:.2f}, must be <= 1.0")
        if self.accounts.income_split is not None and len(self.accounts.income_split) != self.accounts.count:
            raise ValueError(f"{self.name}: income_split length must match accounts.count")


def _load_one(path: Path) -> ArchetypeConfig:
    raw = yaml.safe_load(path.read_text())
    return ArchetypeConfig(
        name=raw["name"],
        employment_type=raw["employment_type"],
        description=raw.get("description", ""),
        income=IncomeConfig(**raw["income"]),
        expenses=ExpenseConfig(**raw["expenses"]),
        discipline=DisciplineConfig(**raw["discipline"]),
        funnel=FunnelConfig(**raw["funnel"]),
        accounts=AccountsConfig(**raw.get("accounts", {"count": 1})),
    )


def load_archetypes(config_dir: Path) -> dict[str, ArchetypeConfig]:
    archetypes: dict[str, ArchetypeConfig] = {}
    for path in sorted(Path(config_dir).glob("*.yaml")):
        cfg = _load_one(path)
        archetypes[cfg.name] = cfg
    return archetypes
