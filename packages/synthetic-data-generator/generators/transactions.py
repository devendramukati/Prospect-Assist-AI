import random
from datetime import date, timedelta

from .archetypes import ArchetypeConfig
from .models import Transaction

ESSENTIAL_MERCHANTS = [
    "BIGBAZAAR SUPERMART", "RELIANCE FRESH", "BBPS-ELECTRICITY BILL",
    "BBPS-GAS BILL", "PHARMEASY MEDICAL", "LOCAL KIRANA STORE",
]
DISCRETIONARY_MERCHANTS = [
    "ZOMATO ORDER", "SWIGGY ORDER", "AMAZON.IN", "PVR CINEMAS",
    "MYNTRA FASHION", "FLIPKART", "ELECTRONICS STORE",
]
DAY1_IMPULSE_DESCRIPTIONS = [
    "POS PURCHASE-ELECTRONICS STORE", "UPI/DR/TRAVEL BOOKING", "ATM CASH WITHDRAWAL",
    "POS PURCHASE-JEWELLERY STORE", "UPI/DR/ONLINE SHOPPING BIG TICKET",
]
SAVINGS_DESCRIPTIONS = [
    "UPI/DR/GROWW MUTUAL FUND SIP", "NEFT-TO-FD ACCOUNT",
    "SIP-HDFC AMC", "RD INSTALLMENT-POST OFFICE",
]
COMPULSORY_DESCRIPTIONS = [
    "ACH DEBIT-HOME LOAN EMI", "NACH-PERSONAL LOAN EMI",
    "RENT TRANSFER-LANDLORD", "NACH-CAR LOAN EMI",
]
BUSINESS_CREDIT_DESCRIPTIONS = ["UPI/CR/CUSTOMER PAYMENT", "UPI/CR/RETAIL SALE", "UPI/CR/WHOLESALE ORDER"]
GIG_CREDIT_DESCRIPTIONS = ["UPI/CR/CLIENT PAYMENT", "NEFT-FREELANCE PAYOUT", "UPI/CR/PROJECT PAYOUT"]
BOUNCE_DESCRIPTION = "ECS RET-INSUFF FUND CHARGES"


def _txn_id(rng: random.Random) -> str:
    return f"txn_{rng.getrandbits(48):012x}"


def month_starts(start: date, months: int) -> list[date]:
    starts = []
    year, month = start.year, start.month
    for _ in range(months):
        starts.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return starts


def _days_in_month(month_start: date) -> int:
    next_month = month_starts(month_start, 2)[1]
    return (next_month - month_start).days


def _income_credits_for_month(
    cfg: ArchetypeConfig, month_start: date, rng: random.Random
) -> list[tuple[date, float, str]]:
    income = cfg.income
    days_in_month = _days_in_month(month_start)

    if income.type == "fixed_salary":
        pay_day = min(income.pay_day or 1, days_in_month)
        amount = income.monthly_amount * (1 + rng.uniform(-income.variance_pct, income.variance_pct))
        return [(month_start.replace(day=pay_day), round(amount, 2), "NEFT-SALARY-EMPLOYER PVT LTD")]

    if income.type == "irregular":
        monthly_total = max(0.0, rng.gauss(income.monthly_mean, income.monthly_mean * income.monthly_stddev_pct))
        n = rng.randint(3, 6)
        shares = [rng.random() for _ in range(n)]
        total_share = sum(shares)
        return [
            (
                month_start.replace(day=rng.randint(1, days_in_month)),
                round(monthly_total * (share / total_share), 2),
                rng.choice(GIG_CREDIT_DESCRIPTIONS),
            )
            for share in shares
        ]

    if income.type == "business_turnover":
        monthly_total = max(
            0.0, rng.gauss(income.monthly_turnover, income.monthly_turnover * income.turnover_variance_pct)
        )
        n = income.txn_count_per_month
        shares = [rng.random() for _ in range(n)]
        total_share = sum(shares)
        return [
            (
                month_start.replace(day=rng.randint(1, days_in_month)),
                round(monthly_total * (share / total_share), 2),
                rng.choice(BUSINESS_CREDIT_DESCRIPTIONS),
            )
            for share in shares
        ]

    raise ValueError(f"Unknown income type: {income.type}")


def _spread_amount(total: float, min_n: int, max_n: int, rng: random.Random) -> list[float]:
    if total <= 0:
        return []
    n = rng.randint(min_n, max_n)
    shares = [rng.random() for _ in range(n)]
    total_share = sum(shares)
    amounts = [round(total * (s / total_share), 2) for s in shares]
    return [a for a in amounts if a > 0]


def generate_month_transactions(
    cfg: ArchetypeConfig,
    account_id: str,
    month_start: date,
    income_scale: float,
    rng: random.Random,
) -> list[Transaction]:
    """Generate one month of transactions for a single account.

    Day-1 spend is modelled as a portion of the essential+discretionary pool
    that lands within 0-2 days of the largest credits that month, rather than
    an amount on top of the configured budget — so a "spends it all" archetype
    is expressed by shifting *when* the money goes, not by exceeding income.
    """
    days_in_month = _days_in_month(month_start)
    transactions: list[Transaction] = []

    credits = _income_credits_for_month(cfg, month_start, rng)
    credits = [(d, round(a * income_scale, 2), desc) for d, a, desc in credits]
    total_income = sum(a for _, a, _ in credits)

    for txn_date, amount, desc in credits:
        transactions.append(
            Transaction(
                id=_txn_id(rng), account_id=account_id, txn_date=txn_date.isoformat(),
                description_raw=desc, amount=amount, direction="credit",
                channel="UPI" if "UPI" in desc else "NEFT",
            )
        )

    essential_pool = cfg.expenses.essential_needs_pct * total_income
    discretionary_pool = cfg.expenses.discretionary_pct * total_income
    compulsory_pool = cfg.expenses.compulsory_obligations_pct * total_income
    savings_pool = cfg.expenses.savings_investment_pct * total_income

    day1_target = min(cfg.discipline.day1_spend_velocity_pct * total_income, essential_pool + discretionary_pool)
    significant_credits = sorted(credits, key=lambda c: c[1], reverse=True)[:3]
    significant_total = sum(a for _, a, _ in significant_credits) or 1.0

    for txn_date, amount, _ in significant_credits:
        allocated = day1_target * (amount / significant_total)
        if allocated <= 0:
            continue
        day1_date = min(txn_date + timedelta(days=rng.randint(0, 2)), month_start.replace(day=days_in_month))
        day1_desc = rng.choice(DAY1_IMPULSE_DESCRIPTIONS)
        transactions.append(
            Transaction(
                id=_txn_id(rng), account_id=account_id, txn_date=day1_date.isoformat(),
                description_raw=day1_desc,
                amount=round(allocated, 2), direction="debit",
                channel="UPI" if "UPI" in day1_desc else ("ATM" if "ATM" in day1_desc else "POS"),
            )
        )
        take_from_essential = min(essential_pool, allocated * 0.5)
        essential_pool -= take_from_essential
        discretionary_pool = max(0.0, discretionary_pool - (allocated - take_from_essential))

    for amount in _spread_amount(essential_pool, 2, 4, rng):
        day = rng.randint(1, days_in_month)
        transactions.append(
            Transaction(
                id=_txn_id(rng), account_id=account_id, txn_date=month_start.replace(day=day).isoformat(),
                description_raw=rng.choice(ESSENTIAL_MERCHANTS), amount=amount, direction="debit", channel="POS",
            )
        )

    for amount in _spread_amount(discretionary_pool, 1, 3, rng):
        day = rng.randint(1, days_in_month)
        transactions.append(
            Transaction(
                id=_txn_id(rng), account_id=account_id, txn_date=month_start.replace(day=day).isoformat(),
                description_raw=rng.choice(DISCRETIONARY_MERCHANTS), amount=amount, direction="debit", channel="UPI",
            )
        )

    if compulsory_pool > 0:
        obligation_day = min(5, days_in_month)
        transactions.append(
            Transaction(
                id=_txn_id(rng), account_id=account_id,
                txn_date=month_start.replace(day=obligation_day).isoformat(),
                description_raw=rng.choice(COMPULSORY_DESCRIPTIONS), amount=round(compulsory_pool, 2),
                direction="debit", channel="ACH",
            )
        )
        if rng.random() < cfg.discipline.bounce_event_probability:
            bounce_day = min(obligation_day + 1, days_in_month)
            transactions.append(
                Transaction(
                    id=_txn_id(rng), account_id=account_id,
                    txn_date=month_start.replace(day=bounce_day).isoformat(),
                    description_raw=BOUNCE_DESCRIPTION, amount=590.0, direction="debit", channel="ACH",
                )
            )

    if savings_pool > 0:
        savings_day = min(rng.randint(25, 28), days_in_month)
        transactions.append(
            Transaction(
                id=_txn_id(rng), account_id=account_id,
                txn_date=month_start.replace(day=savings_day).isoformat(),
                description_raw=rng.choice(SAVINGS_DESCRIPTIONS), amount=round(savings_pool, 2),
                direction="debit", channel="UPI",
            )
        )

    return transactions
