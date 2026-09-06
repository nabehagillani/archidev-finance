import io
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.services.ledger_service import post_invoice_issued, post_invoice_payment
from app.models.user import User
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus, Payment
from app.models.audit import AuditLog
from app.schemas.invoice import InvoiceCreate

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _next_invoice_number(db: Session, company_id: str) -> str:
    count = db.query(Invoice).filter(Invoice.company_id == company_id).count()
    return f"INV-{1000 + count + 1}"


@router.get("")
def list_invoices(db: Session = Depends(get_db), user: User = Depends(get_current_user), status: str | None = None):
    q = db.query(Invoice).filter(Invoice.company_id == user.company_id)
    if status:
        q = q.filter(Invoice.status == status)
    rows = q.order_by(Invoice.invoice_date.desc()).all()
    return [
        {
            "id": r.id, "invoice_number": r.invoice_number, "customer_id": r.customer_id,
            "due_date": r.due_date, "total": float(r.total), "amount_paid": float(r.amount_paid),
            "balance_due": r.balance_due, "status": r.status.value,
        } for r in rows
    ]


@router.post("")
def create_invoice(
    payload: InvoiceCreate, db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_invoice")),
):
    subtotal = sum(i.quantity * i.unit_price for i in payload.items)
    tax_total = sum(i.quantity * i.unit_price * (i.tax_rate / 100) for i in payload.items)
    total = subtotal + tax_total - payload.discount_amount

    inv = Invoice(
        company_id=user.company_id, invoice_number=_next_invoice_number(db, user.company_id),
        customer_id=payload.customer_id, invoice_date=payload.invoice_date, due_date=payload.due_date,
        subtotal=subtotal, tax_amount=tax_total, discount_amount=payload.discount_amount,
        total=total, status=InvoiceStatus.DRAFT,
    )
    db.add(inv)
    db.flush()
    for item in payload.items:
        db.add(InvoiceItem(
            invoice_id=inv.id, description=item.description, quantity=item.quantity,
            unit_price=item.unit_price, tax_rate=item.tax_rate,
            line_total=item.quantity * item.unit_price * (1 + item.tax_rate / 100),
        ))
    db.commit()
    db.refresh(inv)
    return {"id": inv.id, "invoice_number": inv.invoice_number, "total": float(inv.total), "status": inv.status.value}


@router.post("/{invoice_id}/send")
def send_invoice(invoice_id: str, db: Session = Depends(get_db), user: User = Depends(require_permission("manage_invoice"))):
    """Marking an invoice as Sent is what creates the AR journal entry
    (Debit AR / Credit Revenue) — a draft invoice has no accounting impact."""
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.company_id == user.company_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    entry = post_invoice_issued(db, user.company_id, inv)
    inv.journal_entry_id = entry.id
    inv.status = InvoiceStatus.SENT
    db.add(AuditLog(company_id=user.company_id, user_id=user.id, action="sent_invoice", module="invoices", record_id=inv.id))
    db.commit()
    return {"status": "sent"}


@router.post("/{invoice_id}/payments")
def record_payment(invoice_id: str, amount: float, db: Session = Depends(get_db), user: User = Depends(require_permission("manage_invoice"))):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.company_id == user.company_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    entry = post_invoice_payment(db, user.company_id, inv, Decimal(str(amount)))
    inv.amount_paid = Decimal(str(float(inv.amount_paid) + amount))
    inv.status = InvoiceStatus.PAID if inv.amount_paid >= inv.total else InvoiceStatus.PARTIALLY_PAID
    db.add(Payment(company_id=user.company_id, invoice_id=inv.id, amount=amount, journal_entry_id=entry.id))
    db.commit()
    return {"status": inv.status.value, "balance_due": inv.balance_due}


@router.get("/{invoice_id}/pdf")
def invoice_pdf(invoice_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Generates an actual PDF (not a stub) using reportlab."""
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.company_id == user.company_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"Invoice {inv.invoice_number}")
    c.setFont("Helvetica", 11)
    c.drawString(50, 725, f"Date: {inv.invoice_date.strftime('%Y-%m-%d')}   Due: {inv.due_date.strftime('%Y-%m-%d')}")
    y = 690
    for item in inv.items:
        c.drawString(50, y, f"{item.description}  x{item.quantity}  @ {item.unit_price}  = {item.line_total}")
        y -= 18
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, f"Total: {inv.total}")
    c.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={inv.invoice_number}.pdf"
    })
