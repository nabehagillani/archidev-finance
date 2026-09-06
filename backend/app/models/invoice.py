import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum, Integer, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Accounts Receivable document: money owed TO the company by a customer."""
    __tablename__ = "invoices"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    subtotal = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    total = Column(Numeric(14, 2), default=0)
    amount_paid = Column(Numeric(14, 2), default=0)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    customer = relationship("Customer")

    @property
    def balance_due(self):
        return float(self.total) - float(self.amount_paid)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0)
    line_total = Column(Numeric(14, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class Bill(Base):
    """Accounts Payable document: money the company owes TO a vendor.
    Mirrors Invoice but on the payable side."""
    __tablename__ = "bills"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    bill_number = Column(String(50), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("expense_categories.id"), nullable=False)
    bill_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    total = Column(Numeric(14, 2), nullable=False)
    amount_paid = Column(Numeric(14, 2), default=0)
    priority = Column(String(20), default="normal")  # low | normal | high
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.SENT)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor")

    @property
    def balance_due(self):
        return float(self.total) - float(self.amount_paid)


class Payment(Base):
    """A payment applied against either an Invoice (money in) or a
    Bill (money out)."""
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    bill_id = Column(String(36), ForeignKey("bills.id"), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    method = Column(String(50))
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), nullable=True)
