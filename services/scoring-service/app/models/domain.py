from pydantic import BaseModel, Field


class Customer(BaseModel):
    id: str
    external_ref: str
    employment_type: str  # salaried | gig | self_employed | business_owner
    created_at: str


class BankAccount(BaseModel):
    id: str
    customer_id: str
    bank_name: str
    masked_account_number: str
    source: str  # upload | aa_pull | synthetic


class Transaction(BaseModel):
    id: str
    account_id: str
    txn_date: str
    description_raw: str
    amount: float
    direction: str  # credit | debit
    channel: str  # UPI | NEFT | IMPS | POS | ACH | ATM
    category: str = "uncategorized"
    subcategory: str | None = None
    confidence_score: float = 0.0
    is_recurring: bool = False


class Statement(BaseModel):
    account_id: str
    period_start: str
    period_end: str
    transactions: list[Transaction] = Field(default_factory=list)


class ApplicationEvent(BaseModel):
    id: str
    customer_id: str
    event_type: str
    event_ts: str
    metadata: dict = Field(default_factory=dict)


class CustomerBundle(BaseModel):
    customer: Customer
    accounts: list[BankAccount]
    statements: list[Statement]
    application_events: list[ApplicationEvent]
