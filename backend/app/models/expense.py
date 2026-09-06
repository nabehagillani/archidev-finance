import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class ExpenseStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    gl_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    monthly_limit = Column(Numeric(14, 2), nullable=True)


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    employee_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=True)
    category_id = Column(String(36), ForeignKey("expense_categories.id"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    payment_method = Column(String(50))
    description = Column(Text)
    receipt_url = Column(String(500), nullable=True)
    status = Column(Enum(ExpenseStatus), default=ExpenseStatus.SUBMITTED)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("ExpenseCategory")
