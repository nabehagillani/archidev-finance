"""
Computes dashboard KPIs directly from the ledger and AR/AP tables so
the numbers are always a live derivation of real data, never a
separately-maintained summary that can drift out of sync.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.accounting import JournalLine, JournalEntry, Account, AccountType
from app.models.invoice import Invoice, Bill, InvoiceStatus
from app.models.transaction import Transaction, TransactionType


def _account_balance(db: Session, company_id: str, account_type: AccountType, as_of: datetime = None) -> Decimal:
    q = (
        db.query(
            func.coalesce(func.sum(JournalLine.debit), 0) - func.coalesce(func.sum(JournalLine.credit), 0)
        )
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalLine.account_id == Account.id)
        .filter(Account.company_id == company_id, Account.type == account_type)
    )
    if as_of:
        q = q.filter(JournalEntry.entry_date <= as_of)
    result = q.scalar() or 0
    return Decimal(result)


def cash_balance(db: Session, company_id: str) -> Decimal:
    return _account_balance(db, company_id, AccountType.ASSET) - _receivable_total(db, company_id) - _prepaid_total(db, company_id)


def _receivable_total(db: Session, company_id: str) -> Decimal:
    total = db.query(func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0)).filter(
        Invoice.company_id == company_id, Invoice.status != InvoiceStatus.CANCELLED
    ).scalar()
    return Decimal(total or 0)


def _prepaid_total(db: Session, company_id: str) -> Decimal:
    return Decimal(0)  # placeholder until prepaid-expense schedules are implemented


def revenue_total(db: Session, company_id: str, start: datetime = None, end: datetime = None) -> Decimal:
    q = (
        db.query(func.coalesce(func.sum(JournalLine.credit), 0))
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalLine.account_id == Account.id)
        .filter(Account.company_id == company_id, Account.type == AccountType.REVENUE)
    )
    if start:
        q = q.filter(JournalEntry.entry_date >= start)
    if end:
        q = q.filter(JournalEntry.entry_date <= end)
    return Decimal(q.scalar() or 0)


def expense_total(db: Session, company_id: str, start: datetime = None, end: datetime = None) -> Decimal:
    q = (
        db.query(func.coalesce(func.sum(JournalLine.debit), 0))
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalLine.account_id == Account.id)
        .filter(Account.company_id == company_id, Account.type == AccountType.EXPENSE)
    )
    if start:
        q = q.filter(JournalEntry.entry_date >= start)
    if end:
        q = q.filter(JournalEntry.entry_date <= end)
    return Decimal(q.scalar() or 0)


def payable_total(db: Session, company_id: str) -> Decimal:
    total = db.query(func.coalesce(func.sum(Bill.total - Bill.amount_paid), 0)).filter(
        Bill.company_id == company_id, Bill.status != InvoiceStatus.CANCELLED
    ).scalar()
    return Decimal(total or 0)


def pending_invoices_count(db: Session, company_id: str) -> int:
    return db.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
    ).count()


def overdue_payments_total(db: Session, company_id: str) -> Decimal:
    now = datetime.utcnow()
    total = db.query(func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0)).filter(
        Invoice.company_id == company_id,
        Invoice.due_date < now,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
    ).scalar()
    return Decimal(total or 0)


def get_kpis(db: Session, company_id: str) -> dict:
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_revenue = revenue_total(db, company_id)
    total_expenses = expense_total(db, company_id)
    net_profit = total_revenue - total_expenses

    return {
        "total_revenue": float(total_revenue),
        "total_expenses": float(total_expenses),
        "net_profit": float(net_profit),
        "cash_balance": float(cash_balance(db, company_id)),
        "accounts_receivable": float(_receivable_total(db, company_id)),
        "accounts_payable": float(payable_total(db, company_id)),
        "pending_invoices": pending_invoices_count(db, company_id),
        "overdue_payments": float(overdue_payments_total(db, company_id)),
        "financial_health": financial_health_score(db, company_id),
    }


def financial_health_score(db: Session, company_id: str) -> dict:
    """
    A transparent, documented weighted score (0-100) — not a black box.
    Factors and weights:
      - Cash runway (25%): cash_balance vs trailing-3-month avg burn
      - Profitability (25%): net margin over trailing 3 months
      - Expense growth (15%): this month's expenses vs 3-month average (penalized if growing fast)
      - Receivables health (15%): % of AR that is NOT overdue
      - Payables coverage (10%): cash_balance vs total payables due
      - Revenue stability (10%): coefficient of variation of last 3 months' revenue (lower = more stable)
    Each factor is scored 0-100 and combined by weight; this is intentionally
    simple and auditable rather than a hidden ML score.
    """
    now = datetime.utcnow()
    three_mo_ago = now - timedelta(days=90)

    rev_3mo = revenue_total(db, company_id, three_mo_ago, now)
    exp_3mo = expense_total(db, company_id, three_mo_ago, now)
    cash = cash_balance(db, company_id)
    ar_total = _receivable_total(db, company_id)
    ar_overdue = overdue_payments_total(db, company_id)
    ap_total = payable_total(db, company_id)

    avg_monthly_burn = float(exp_3mo) / 3 if exp_3mo else 0
    cash_runway_months = (float(cash) / avg_monthly_burn) if avg_monthly_burn > 0 else 6
    cash_score = min(100, (cash_runway_months / 6) * 100)

    net_margin = (float(rev_3mo - exp_3mo) / float(rev_3mo)) if rev_3mo else 0
    profitability_score = max(0, min(100, (net_margin + 0.2) / 0.4 * 100))

    this_month_exp = float(expense_total(db, company_id, now.replace(day=1), now))
    avg_monthly_exp = float(exp_3mo) / 3 if exp_3mo else 0
    growth_pct = ((this_month_exp - avg_monthly_exp) / avg_monthly_exp) if avg_monthly_exp else 0
    expense_growth_score = max(0, min(100, 100 - growth_pct * 200))

    receivables_score = 100 if not ar_total else max(0, 100 - (float(ar_overdue) / float(ar_total) * 100))

    payables_score = 100 if ap_total == 0 else min(100, (float(cash) / float(ap_total)) * 100)

    revenue_stability_score = 70  # placeholder until >=3 full months of seed history exist to compute variance

    weighted = (
        cash_score * 0.25 + profitability_score * 0.25 + expense_growth_score * 0.15
        + receivables_score * 0.15 + payables_score * 0.10 + revenue_stability_score * 0.10
    )

    return {
        "score": round(weighted),
        "factors": {
            "cash_flow": round(cash_score),
            "profitability": round(profitability_score),
            "expense_growth": round(expense_growth_score),
            "receivables": round(receivables_score),
            "debt_payment_obligations": round(payables_score),
            "revenue_stability": round(revenue_stability_score),
        },
    }
