import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum, Boolean
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class MatchStatus(str, enum.Enum):
    UNMATCHED = "unmatched"
    MATCHED = "matched"
    DUPLICATE = "duplicate"
    MISMATCH = "mismatch"


class BankTransaction(Base):
    """A raw line from an uploaded bank statement, before reconciliation."""
    __tablename__ = "bank_transactions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    bank_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(500))
    amount = Column(Numeric(14, 2), nullable=False)
    external_ref = Column(String(120))
    match_status = Column(Enum(MatchStatus), default=MatchStatus.UNMATCHED)
    matched_transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Reconciliation(Base):
    """One reconciliation run/batch, summarizing the match results of
    a single bank statement upload."""
    __tablename__ = "reconciliations"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    bank_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    run_at = Column(DateTime, default=datetime.utcnow)
    total_bank_lines = Column(Numeric(10, 0), default=0)
    matched_count = Column(Numeric(10, 0), default=0)
    unmatched_count = Column(Numeric(10, 0), default=0)
    duplicate_count = Column(Numeric(10, 0), default=0)
    match_rate_pct = Column(Numeric(5, 2), default=0)
