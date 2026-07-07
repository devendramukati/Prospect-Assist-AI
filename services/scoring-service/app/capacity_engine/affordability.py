from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_LOAN_PRODUCTS_PATH = Path(__file__).parent / "loan_products.yaml"


@lru_cache(maxsize=1)
def _load_loan_products(path: str = str(DEFAULT_LOAN_PRODUCTS_PATH)) -> dict:
    return yaml.safe_load(Path(path).read_text())


def _max_principal_from_emi(emi: float, annual_rate_pct: float, tenure_months: int) -> float:
    if emi <= 0:
        return 0.0
    monthly_rate = annual_rate_pct / 1200
    if monthly_rate == 0:
        return round(emi * tenure_months, 2)
    factor = (1 + monthly_rate) ** tenure_months
    principal = emi * (factor - 1) / (monthly_rate * factor)
    return round(principal, 2)


def compute_affordability(monthly_income: float, existing_compulsory_obligations: float) -> dict:
    """For each loan product, the FOIR cap bounds *total* obligations
    (existing + new), so the new loan's max EMI is whatever headroom is left
    after existing compulsory obligations. Home/Mortgage are explicitly
    flagged as needing a property-value/LTV input the bank statement alone
    can't supply — the principal figure here is an income-side ceiling only.
    """
    products = _load_loan_products()
    results = {}
    for product_name, cfg in products.items():
        max_total_obligation = cfg["foir_cap"] * monthly_income
        max_new_emi = max(0.0, max_total_obligation - existing_compulsory_obligations)
        results[product_name] = {
            "max_affordable_emi": round(max_new_emi, 2),
            "max_affordable_principal": _max_principal_from_emi(max_new_emi, cfg["annual_rate_pct"], cfg["tenure_months"]),
            "requires_collateral_input": cfg.get("requires_collateral_input", False),
        }
    return results
