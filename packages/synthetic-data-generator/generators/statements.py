import random
from datetime import date

from .archetypes import ArchetypeConfig
from .models import BankAccount, Statement
from .transactions import generate_month_transactions, month_starts

BANK_NAMES = ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Kotak Mahindra Bank"]


def _masked_account_number(rng: random.Random) -> str:
    return f"XXXXXXXX{rng.randint(1000, 9999)}"


def build_accounts_and_statements(
    cfg: ArchetypeConfig,
    customer_id: str,
    period_start: date,
    period_months: int,
    rng: random.Random,
) -> tuple[list[BankAccount], list[Statement]]:
    accounts: list[BankAccount] = []
    statements: list[Statement] = []

    n_accounts = cfg.accounts.count
    splits = cfg.accounts.income_split or [1.0 / n_accounts] * n_accounts
    sources = ["upload"] + ["aa_pull"] * (n_accounts - 1)
    starts = month_starts(period_start, period_months)

    for i in range(n_accounts):
        account_id = f"acct_{rng.getrandbits(32):08x}"
        accounts.append(
            BankAccount(
                id=account_id, customer_id=customer_id,
                bank_name=rng.choice(BANK_NAMES),
                masked_account_number=_masked_account_number(rng),
                source=sources[i],
            )
        )

        all_txns = []
        for m_start in starts:
            all_txns.extend(generate_month_transactions(cfg, account_id, m_start, splits[i], rng))

        statements.append(
            Statement(
                account_id=account_id,
                period_start=period_start.isoformat(),
                period_end=starts[-1].isoformat(),
                transactions=sorted(all_txns, key=lambda t: t.txn_date),
            )
        )

    return accounts, statements
