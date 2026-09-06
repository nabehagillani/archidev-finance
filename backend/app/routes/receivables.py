from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus

router = APIRouter(prefix="/api/receivables", tags=["receivables"])


@router.get("/aging")
def aging_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """0-30 / 31-60 / 61-90 / 90+ day aging buckets, computed live from
    open invoices — this is real data, not a mocked report."""
    now = datetime.utcnow()
    buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    high_risk = []

    invoices = db.query(Invoice).filter(
        Invoice.company_id == user.company_id,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]),
    ).all()

    for inv in invoices:
        days_overdue = (now - inv.due_date).days
        balance = inv.balance_due
        if days_overdue <= 30:
            buckets["0-30"] += balance
        elif days_overdue <= 60:
            buckets["31-60"] += balance
        elif days_overdue <= 90:
            buckets["61-90"] += balance
        else:
            buckets["90+"] += balance
            high_risk.append({"invoice_number": inv.invoice_number, "days_overdue": days_overdue, "balance_due": balance})

    return {
        "total_receivable": sum(buckets.values()),
        "buckets": buckets,
        "high_risk_overdue": high_risk,
    }
