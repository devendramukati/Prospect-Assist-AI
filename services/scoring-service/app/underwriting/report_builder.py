from datetime import datetime, timezone


def build_underwriting_report(customer: dict, assessment: dict, score: dict) -> dict:
    """Reshapes the lead-scoring output into a loan-officer-readable summary:
    the income band, FOIR/affordability, discipline flags, and the tier +
    explanation together in one exportable document, rather than the raw
    nested API response shape a UI happens to use internally.
    """
    income = assessment["income"]
    discipline = assessment["discipline"]

    income_summary = {
        "method": income["method"],
        "monthly_income_estimate": income["monthly_income_estimate"],
        "confidence_band": (
            {"low": income["confidence_low"], "high": income["confidence_high"]}
            if income["confidence_low"] is not None
            else None
        ),
        "income_stability_score": income["income_stability_score"],
    }

    risk_flags = []
    if discipline["bounce"]["bounce_flag"]:
        risk_flags.append(f"{discipline['bounce']['bounce_count']} bounced payment(s) detected")
    if discipline["day1_spend_velocity"]["day1_spend_velocity_pct"] >= 0.5:
        pct = discipline["day1_spend_velocity"]["day1_spend_velocity_pct"]
        risk_flags.append(f"High day-1 spend velocity ({pct:.0%} of income spent within 2 days of credit)")
    if discipline["balance"]["went_negative"]:
        risk_flags.append("Account balance went negative during the observed period")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scoring_version": score["scoring_version"],
        "customer": {
            "external_ref": customer["external_ref"],
            "employment_type": customer["employment_type"],
            "full_name": customer.get("kyc", {}).get("full_name"),
            "account_count": customer.get("account_count"),
        },
        "income_summary": income_summary,
        "affordability": {
            "capacity_basis": assessment["capacity_basis"],
            "disposable_income": assessment["disposable_income"]["disposable_income"],
            "foir_pct": assessment["disposable_income"]["foir_pct"],
            "by_product": assessment["affordability_by_product"],
        },
        "risk_flags": risk_flags,
        "lead_tier": score["tier"],
        "capped_by": score["capped_by"],
        "composite_score": score["composite_score"],
        "explanation": score["explanation"],
    }
