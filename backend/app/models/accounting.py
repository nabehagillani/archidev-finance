"""
Real double-entry bookkeeping core.

- Account: the chart of accounts (Asset/Liability/Equity/Revenue/Expense).
- JournalEntry + JournalLine: every financial event is recorded as a
  balanced set of debit/credit lines. Every other module (transactions,
  invoices, expenses, payments) posts through here rather than mutating
  balances directly, so the Balance Sheet and P&L are always derivable
  and always in balance.
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Numeric, ForeignKey, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


# Accounts with a normal debit balance increase on debit, decrease on
# credit; ASSET and EXPENSE are debit-normal, the rest are credit-normal.
DEBIT_NORMAL_TYPES = {AccountType.ASSET, AccountType.EXPENSE}


class Account(Base):
    """A single line of the chart of accounts, e.g. '1000 Cash',
    '4000 Sales Revenue', '6100 Rent Expense'."""
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(AccountType), nullable=False)
    is_bank_account = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    parent_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=True)

    parent = relationship("Account", remote_side=[id])


class JournalEntry(Base):
    """One balanced accounting event. sum(debits) must equal sum(credits)."""
    __tablename__ = "journal_entries"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    entry_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    memo = Column(Text)
    source_module = Column(String(50))   # 'transaction' | 'invoice' | 'expense' | 'payment'
    source_id = Column(String(36))       # id of the record that generated this entry
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    debit = Column(Numeric(14, 2), default=0)
    credit = Column(Numeric(14, 2), default=0)
    description = Column(String(255))

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


DEFAULT_CHART_OF_ACCOUNTS = [
    # code, name, type, is_bank_account
    ("1000", "Cash and Bank", AccountType.ASSET, True),
    ("1100", "Accounts Receivable", AccountType.ASSET, False),
    ("1500", "Prepaid Expenses", AccountType.ASSET, False),
    ("2000", "Accounts Payable", AccountType.LIABILITY, False),
    ("2100", "Taxes Payable", AccountType.LIABILITY, False),
    ("3000", "Owner's Equity", AccountType.EQUITY, False),
    ("3900", "Retained Earnings", AccountType.EQUITY, False),
    ("4000", "Sales Revenue", AccountType.REVENUE, False),
    ("4900", "Other Income", AccountType.REVENUE, False),
    ("6000", "Salaries & Wages", AccountType.EXPENSE, False),
    ("6100", "Rent", AccountType.EXPENSE, False),
    ("6200", "Utilities", AccountType.EXPENSE, False),
    ("6300", "Software & Subscriptions", AccountType.EXPENSE, False),
    ("6400", "Marketing", AccountType.EXPENSE, False),
    ("6500", "Office Supplies", AccountType.EXPENSE, False),
    ("6900", "Other Operating Expenses", AccountType.EXPENSE, False),
]
