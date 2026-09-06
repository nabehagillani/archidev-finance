from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.services.ledger_service import post_bill_received, post_bill_payment
from app.models.user import User
from app.models.invoice import Bill, InvoiceStatus, Payment
from app.models.expense import ExpenseCategory
from app.models.audit import AuditLog
from app.schemas.bill import BillCreate

router = APIRouter(prefix="/api/payables", tags=["payables"])


def _next_bill_number(db: Session, company_id: str) -> str:
    count = db.query(Bill).filter(Bill.company_id == company_id).count()
    return f"BILL-{1000 + count + 1}"


@router.get("")
def list_payables(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bills = db.query(Bill).filter(Bill.company_id == user.company_id).all()
    now = datetime.utcnow()
    upcoming_alerts = [
        {"bill_number": b.bill_number, "due_date": b.due_date, "balance_due": b.balance_due}
        for b in bills if b.status != InvoiceStatus.PAID and 0 <= (b.due_date - now).days <= 7
    ]
    return {
        "total_payable": sum(b.balance_due for b in bills if b.status != InvoiceStatus.PAID),
        "paid": sum(float(b.amount_paid) for b in bills),
        "pending": sum(b.balance_due for b in bills if b.status in (InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID)),
        "overdue": sum(b.balance_due for b in bills if b.due_date < now and b.status != InvoiceStatus.PAID),
        "upcoming_payment_alerts": upcoming_alerts,
        "bills": [
            {"id": b.id, "bill_number": b.bill_number, "vendor_id": b.vendor_id, "due_date": b.due_date,
             "total": float(b.total), "balance_due": b.balance_due, "priority": b.priority, "status": b.status.value}
            for b in bills
        ],
    }


@router.post("")
def create_bill(
    payload: BillCreate, db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_expense")),
):
    """Recording a vendor bill immediately posts the AP journal entry
    (Debit the bill's expense category / Credit Accounts Payable) —
    unlike invoices there's no separate draft/send step, since a bill
    is a liability the moment it's received, not something the company
    issues and controls the timing of."""
    category = db.query(ExpenseCategory).filter(
        ExpenseCategory.id == payload.category_id, ExpenseCategory.company_id == user.company_id,
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="Unknown expense category")

    bill = Bill(
        company_id=user.company_id, bill_number=_next_bill_number(db, user.company_id),
        vendor_id=payload.vendor_id, category_id=payload.category_id,
        bill_date=payload.bill_date, due_date=payload.due_date,
        total=payload.total, priority=payload.priority, status=InvoiceStatus.SENT,
    )
    db.add(bill)
    db.flush()
    entry = post_bill_received(db, user.company_id, bill, category.gl_account_id)
    bill.journal_entry_id = entry.id

    db.add(AuditLog(company_id=user.company_id, user_id=user.id, action="created_bill", module="payables", record_id=bill.id))
    db.commit()
    db.refresh(bill)
    return {"id": bill.id, "bill_number": bill.bill_number, "total": float(bill.total), "status": bill.status.value}


@router.post("/{bill_id}/payments")
def pay_bill(
    bill_id: str, amount: float, db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_expense")),
):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.company_id == user.company_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if amount <= 0 or amount > bill.balance_due:
        raise HTTPException(status_code=400, detail=f"Amount must be between 0 and the balance due ({bill.balance_due})")

    entry = post_bill_payment(db, user.company_id, bill, Decimal(str(amount)))
    bill.amount_paid = Decimal(str(float(bill.amount_paid) + amount))
    bill.status = InvoiceStatus.PAID if bill.amount_paid >= bill.total else InvoiceStatus.PARTIALLY_PAID
    db.add(Payment(company_id=user.company_id, bill_id=bill.id, amount=amount, journal_entry_id=entry.id))

    db.add(AuditLog(company_id=user.company_id, user_id=user.id, action="paid_bill", module="payables", record_id=bill.id, new_value=str(amount)))
    db.commit()
    return {"status": bill.status.value, "balance_due": bill.balance_due}

