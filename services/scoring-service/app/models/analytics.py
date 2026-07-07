from pydantic import BaseModel


class IncomeEstimate(BaseModel):
    method: str  # fixed_salary | rolling_avg | turnover_margin
    monthly_income_estimate: float
    income_stability_score: float  # 0..1, higher = more predictable
    sample_size: int
    confidence_low: float | None = None
    confidence_high: float | None = None
    supporting_evidence: dict = {}
