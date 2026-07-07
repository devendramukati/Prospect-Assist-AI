from app.income_engine import business_owner, gig_irregular, salaried
from app.models.analytics import IncomeEstimate
from app.models.domain import Transaction


def estimate_income(employment_type: str, transactions: list[Transaction], industry: str | None = None) -> IncomeEstimate:
    """Dispatches to the income path matching the customer's employment
    type. Real-world business/professional income classification (industry
    code) would come from KYC/business-registration data, not the bank
    statement itself — this MVP defaults to a conservative margin band when
    it isn't supplied.
    """
    if employment_type == "salaried":
        result = salaried.estimate_salaried_income(transactions)
        return IncomeEstimate(
            method=result["method"],
            monthly_income_estimate=result["monthly_income_estimate"],
            income_stability_score=result["income_stability_score"],
            sample_size=result["sample_size"],
        )

    if employment_type == "gig":
        result = gig_irregular.estimate_gig_income(transactions)
        return IncomeEstimate(
            method=result["method"],
            monthly_income_estimate=result["monthly_income_estimate"],
            income_stability_score=result["income_stability_score"],
            sample_size=result["sample_size"],
        )

    if employment_type in ("self_employed", "business_owner"):
        result = business_owner.estimate_business_income(transactions, industry=industry)
        return IncomeEstimate(
            method=result["method"],
            monthly_income_estimate=result["monthly_income_estimate_mid"],
            # Inherently less certain than a directly-observed salary figure;
            # not derived from the coefficient of variation of a single series.
            income_stability_score=0.5,
            confidence_low=result["monthly_income_estimate_low"],
            confidence_high=result["monthly_income_estimate_high"],
            sample_size=result["sample_size"],
            supporting_evidence={"monthly_turnover": result["monthly_turnover"]},
        )

    raise ValueError(f"Unknown employment_type: {employment_type}")
