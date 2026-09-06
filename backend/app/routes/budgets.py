from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.models.user import User
from app.models.budget import Budget
from app.models.expense import ExpenseCategory
from app.models.accounting import Account, AccountType, JournalLine, JournalEntry
from app.models.notification import Notification, NotificationSeverity

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


def _actual_spend_for_gl_account(db: Session, company_id: str, gl_account_id: str, start: datetime) -> float:
    """Reads actual spend straight from the ledger for the category's GL
    account, so it reflects both approved-Expense-workflow spend and
    directly-posted Transaction spend (e.g. an ad platform charge
    imported from a bank feed) — whichever path the money actually
    took to reach the books."""
    total = (
        db.query(func.coalesce(func.sum(JournalLine.debit), 0))
        .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .filter(JournalLine.account_id == gl_account_id, JournalEntry.entry_date >= start)
        .scalar()
    )
    return float(total or 0)


@router.get("")
def list_budgets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    budgets = db.query(Budget).filter(
        Budget.company_id == user.company_id, Budget.period_year == now.year, Budget.period_month == now.month,
    ).all()

    results = []
    for b in budgets:
        cat = db.query(ExpenseCategory).get(b.category_id)
        actual_total = _actual_spend_for_gl_account(db, user.company_id, cat.gl_account_id, now.replace(day=1))
        pct = round((actual_total / float(b.amount)) * 100, 1) if b.amount else 0

        if pct >= 100:
            db.add(Notification(
                company_id=user.company_id, type="budget_exceeded", severity=NotificationSeverity.CRITICAL,
                message=f"{cat.name} spending has exceeded its budget ({pct}% used).",
            ))
        elif pct >= 85:
            db.add(Notification(
                company_id=user.company_id, type="budget_exceeded", severity=NotificationSeverity.WARNING,
                message=f"{cat.name} spending is approaching its budget ({pct}% used).",
            ))

        results.append({
            "category": cat.name, "budget": float(b.amount), "actual": actual_total,
            "remaining": float(b.amount) - actual_total, "percent_used": pct,
        })
    db.commit()
    return results


@router.post("")
def set_budget(
    category_id: str, amount: float, year: int, month: int,
    db: Session = Depends(get_db), user: User = Depends(require_permission("manage_budget")),
):
    existing = db.query(Budget).filter(
        Budget.company_id == user.company_id, Budget.category_id == category_id,
        Budget.period_year == year, Budget.period_month == month,
    ).first()
    if existing:
        existing.amount = amount
    else:
        db.add(Budget(company_id=user.company_id, category_id=category_id, period_year=year, period_month=month, amount=amount))
    db.commit()
    return {"status": "saved"}
