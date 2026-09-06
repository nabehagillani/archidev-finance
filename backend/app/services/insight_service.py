"""
Rule-based financial insight generation. Each rule reads real ledger/
AR data, computes an actual number, and only fires when a concrete
threshold is crossed — insights are never invented, and every one
carries the supporting_data that produced it so a user can verify the
claim rather than trust it blindly.
"""
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services import dashboard_service
from app.models.insight import FinancialInsight, InsightSeverity
from app.models.invoice import Invoice, InvoiceStatus
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.accounting import Account, AccountType, JournalLine, JournalEntry


def _category_expense_totals(db: Session, company_id: str, start, end):
    """
    Sourced directly from the general ledger (grouped by expense GL
    account) rather than the Expense-submission table alone. Expense
    category spend can reach the books two ways — an employee-submitted
    Expense that gets approved, or a directly-entered/imported
    Transaction (e.g. an ad-spend bank charge) — and both post to the
    same GL account via ledger_service. Reading from the ledger means
    this rule (and the dashboard's expense-growth factor) sees the true
    total regardless of which path the spend came in through, instead
    of silently missing transaction-sourced spend.
    """
    rows = (
        db.query(Account.name, func.coalesce(func.sum(JournalLine.debit), 0))
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .filter(Account.company_id == company_id, Account.type == AccountType.EXPENSE,
                JournalEntry.entry_date >= start, JournalEntry.entry_date < end)
        .group_by(Account.name).all()
    )
    return {name: float(total) for name, total in rows}


def generate_insights(db: Session, company_id: str) -> list[FinancialInsight]:
    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = this_month_start - relativedelta(months=1)

    this_month = _category_expense_totals(db, company_id, this_month_start, now)
    last_month = _category_expense_totals(db, company_id, last_month_start, this_month_start)

    insights = []

    # --- Expense Alert: category spend jumped >=20% month over month ---
    for cat, amount in this_month.items():
        prev = last_month.get(cat, 0)
        if prev > 0:
            pct_change = ((amount - prev) / prev) * 100
            if pct_change >= 20:
                insights.append(FinancialInsight(
                    company_id=company_id, category="expense_alert",
                    severity=InsightSeverity.WARNING if pct_change < 50 else InsightSeverity.CRITICAL,
                    explanation=f"{cat} expenses increased {pct_change:.0f}% compared with last month.",
                    supporting_data=json.dumps({"category": cat, "this_month": amount, "last_month": prev}),
                    recommended_action=f"Review recent {cat} transactions for one-off or unapproved spend.",
                ))

    # --- Revenue Insight: 4 consecutive months of growth ---
    monthly_revenue = []
    for i in range(3, -1, -1):
        m_start = this_month_start - relativedelta(months=i)
        m_end = m_start + relativedelta(months=1)
        monthly_revenue.append(float(dashboard_service.revenue_total(db, company_id, m_start, m_end)))
    if len(monthly_revenue) == 4 and all(monthly_revenue[i] < monthly_revenue[i + 1] for i in range(3)):
        insights.append(FinancialInsight(
            company_id=company_id, category="revenue", severity=InsightSeverity.INFO,
            explanation="Revenue has increased consistently for the last 4 months.",
            supporting_data=json.dumps({"monthly_revenue": monthly_revenue}),
            recommended_action="Consider whether current growth capacity (staffing, cash) can sustain the trend.",
        ))

    # --- Cash Flow Risk: projected runway below threshold ---
    cash = float(dashboard_service.cash_balance(db, company_id))
    avg_burn = float(dashboard_service.expense_total(db, company_id, this_month_start - relativedelta(months=3), now)) / 3
    if avg_burn > 0 and (cash / avg_burn) < 1:
        insights.append(FinancialInsight(
            company_id=company_id, category="cash_flow_risk", severity=InsightSeverity.CRITICAL,
            explanation="Projected cash balance may fall below the recommended threshold next month.",
            supporting_data=json.dumps({"cash_balance": cash, "avg_monthly_burn": avg_burn}),
            recommended_action="Delay non-essential spending and accelerate collection of outstanding invoices.",
        ))

    # --- Payment Risk: customers overdue > 60 days ---
    overdue_60 = db.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
        Invoice.due_date < now - timedelta(days=60),
    ).all()
    if overdue_60:
        insights.append(FinancialInsight(
            company_id=company_id, category="payment_risk", severity=InsightSeverity.WARNING,
            explanation=f"{len(overdue_60)} customers have invoices overdue by more than 60 days.",
            supporting_data=json.dumps({"invoice_numbers": [i.invoice_number for i in overdue_60]}),
            recommended_action="Prioritize collections outreach for these accounts before extending further credit.",
        ))

    # --- Cost Saving: category is a large share of total opex ---
    total_opex = sum(this_month.values())
    if total_opex > 0:
        for cat, amount in this_month.items():
            share = (amount / total_opex) * 100
            if "software" in cat.lower() and share >= 10:
                insights.append(FinancialInsight(
                    company_id=company_id, category="cost_saving", severity=InsightSeverity.INFO,
                    explanation=f"{cat} represents {share:.0f}% of operating expenses this month.",
                    supporting_data=json.dumps({"category": cat, "amount": amount, "share_pct": share}),
                    recommended_action="Audit active subscriptions for unused seats or overlapping tools.",
                ))

    for ins in insights:
        db.add(ins)
    db.commit()
    return insights
