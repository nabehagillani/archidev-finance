import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    CLEARED = "cleared"
    RECONCILED = "reconciled"
    VOID = "void"


class TransactionCategory(Base):
    """User-facing category, distinct from the underlying GL account,
    e.g. 'Software/Subscription' maps to GL account 6300."""
    __tablename__ = "transaction_categories"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    gl_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    keyword_rules = Column(Text)  # comma-separated keywords used for auto-categorization


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    category_id = Column(String(36), ForeignKey("transaction_categories.id"), nullable=True)
    bank_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    payment_method = Column(String(50))
    reference = Column(String(120))
    status = Column(Enum(TransactionStatus), default=TransactionStatus.CLEARED)
    notes = Column(Text)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("TransactionCategory")
