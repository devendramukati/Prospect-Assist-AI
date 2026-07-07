from app.underwriting.report_builder import build_underwriting_report

CUSTOMER = {"external_ref": "demo-001", "employment_type": "salaried"}

ASSESSMENT = {
    "income": {
        "method": "fixed_salary", "monthly_income_estimate": 75000.0, "income_stability_score": 0.95,
        "sample_size": 6, "confidence_low": None, "confidence_high": None, "supporting_evidence": {},
    },
    "capacity_basis": "net_income",
    "disposable_income": {"disposable_income": 50000.0, "foir_pct": 0.15},
    "affordability_by_product": {
        "personal_loan": {"max_affordable_emi": 26500.0, "max_affordable_principal": 1000000.0, "requires_collateral_input": False},
    },
    "discipline": {
        "day1_spend_velocity": {"day1_spend_velocity_pct": 0.15, "months_observed": 6},
        "bounce": {"bounce_count": 0, "bounce_flag": False},
        "balance": {"minimum_running_balance": 0.0, "low_balance_event_count": 0, "went_negative": False},
    },
}

SCORE = {
    "scoring_version": "v1",
    "tier": "Serious",
    "capped_by": None,
    "composite_score": 0.9,
    "explanation": {"composite_score": 0.9, "tier": "Serious", "capped_by": None, "gate_reasons": [], "factors": []},
}


def test_report_includes_no_risk_flags_for_clean_profile():
    report = build_underwriting_report(CUSTOMER, ASSESSMENT, SCORE)
    assert report["risk_flags"] == []
    assert report["lead_tier"] == "Serious"
    assert report["income_summary"]["confidence_band"] is None


def test_report_flags_bounce_and_day1_and_negative_balance():
    risky_assessment = {
        **ASSESSMENT,
        "discipline": {
            "day1_spend_velocity": {"day1_spend_velocity_pct": 0.7, "months_observed": 6},
            "bounce": {"bounce_count": 2, "bounce_flag": True},
            "balance": {"minimum_running_balance": -500.0, "low_balance_event_count": 3, "went_negative": True},
        },
    }
    report = build_underwriting_report(CUSTOMER, risky_assessment, SCORE)
    assert len(report["risk_flags"]) == 3
    assert any("bounced payment" in flag for flag in report["risk_flags"])
    assert any("day-1 spend velocity" in flag for flag in report["risk_flags"])
    assert any("negative" in flag for flag in report["risk_flags"])


def test_report_includes_confidence_band_for_business_income():
    business_assessment = {
        **ASSESSMENT,
        "income": {**ASSESSMENT["income"], "confidence_low": 60000.0, "confidence_high": 120000.0},
    }
    report = build_underwriting_report(CUSTOMER, business_assessment, SCORE)
    assert report["income_summary"]["confidence_band"] == {"low": 60000.0, "high": 120000.0}
