from dataclasses import dataclass, field


@dataclass
class Customer:
    id: str
    external_ref: str
    employment_type: str
    archetype: str
    created_at: str


@dataclass
class BankAccount:
    id: str
    customer_id: str
    bank_name: str
    masked_account_number: str
    source: str  # upload | aa_pull | synthetic


@dataclass
class Transaction:
    id: str
    account_id: str
    txn_date: str  # ISO date
    description_raw: str
    amount: float
    direction: str  # credit | debit
    channel: str  # UPI | NEFT | IMPS | POS | ACH | ATM


@dataclass
class Statement:
    account_id: str
    period_start: str
    period_end: str
    transactions: list[Transaction] = field(default_factory=list)


@dataclass
class ApplicationEvent:
    id: str
    customer_id: str
    event_type: str
    event_ts: str  # ISO datetime
    metadata: dict = field(default_factory=dict)
