"""
The double-entry posting layer. Every module that touches money calls
into here rather than writing journal lines itself, so the books can
never go out of balance and the Balance Sheet/P&L are always accurate
derivations of the ledger rather than separately-maintained numbers.
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.accounting import JournalEntry, JournalLine, Account


def _get_account(db: Session, company_id: str, code: str) -> Account:
    acct = db.query(Account).filter(
        Account.company_id == company_id, Account.code == code
    ).first()
    if not acct:
        raise ValueError(f"Chart of accounts is missing required account {code}")
    return acct


def post_balanced_entry(
    db: Session, company_id: str, memo: str, source_module: str, source_id: str,
    debit_account_id: str, credit_account_id: str, amount: Decimal,
    created_by: str | None = None, entry_date: datetime | None = None,
) -> JournalEntry:
    """Post a simple two-line balanced journal entry (the common case).

    entry_date should be the real-world date of the underlying event
    (the transaction's date, the invoice's date, etc.) — NOT the moment
    it happened to be entered into the system. Every period-based
    report (P&L, Balance Sheet as-of, monthly forecasts, the financial
    health score) filters on this field, so a backdated entry must
    carry its real date or those reports silently misattribute it to
    whatever month it was typed in."""
    entry = JournalEntry(
        company_id=company_id, memo=memo, source_module=source_module,
        source_id=source_id, created_by=created_by,
        entry_date=entry_date or datetime.utcnow(),
    )
    entry.lines = [
        JournalLine(account_id=debit_account_id, debit=amount, credit=0, description=memo),
        JournalLine(account_id=credit_account_id, debit=0, credit=amount, description=memo),
    ]
    db.add(entry)
    db.flush()
    return entry


def post_transaction(db: Session, company_id: str, transaction) -> JournalEntry:
    """
    Income  -> Debit bank/cash account,          Credit revenue account (via category)
    Expense -> Debit expense account (category),  Credit bank/cash account
    Transfer-> Debit destination handled by caller; here we just move
               between two accounts referenced on the transaction.
    """
    from app.models.transaction import TransactionType

    if transaction.type == TransactionType.INCOME:
        revenue_account_id = transaction.category.gl_account_id if transaction.category else _get_account(db, company_id, "4900").id
        return post_balanced_entry(
            db, company_id, f"Income: {transaction.description}", "transaction", transaction.id,
            debit_account_id=transaction.bank_account_id,
            credit_account_id=revenue_account_id,
            amount=transaction.amount, created_by=transaction.created_by, entry_date=transaction.date,
        )
    elif transaction.type == TransactionType.EXPENSE:
        expense_account_id = transaction.category.gl_account_id if transaction.category else _get_account(db, company_id, "6900").id
        return post_balanced_entry(
            db, company_id, f"Expense: {transaction.description}", "transaction", transaction.id,
            debit_account_id=expense_account_id,
            credit_account_id=transaction.bank_account_id,
            amount=transaction.amount, created_by=transaction.created_by, entry_date=transaction.date,
        )
    else:
        raise ValueError("Transfers require both a source and destination account")


def post_invoice_issued(db: Session, company_id: str, invoice) -> JournalEntry:
    """Issuing an invoice: Debit Accounts Receivable, Credit Sales Revenue."""
    ar = _get_account(db, company_id, "1100")
    revenue = _get_account(db, company_id, "4000")
    return post_balanced_entry(
        db, company_id, f"Invoice {invoice.invoice_number} issued", "invoice", invoice.id,
        debit_account_id=ar.id, credit_account_id=revenue.id, amount=invoice.total, entry_date=invoice.invoice_date,
    )


def post_invoice_payment(db: Session, company_id: str, invoice, amount: Decimal) -> JournalEntry:
    """Customer pays an invoice: Debit Cash, Credit Accounts Receivable."""
    cash = _get_account(db, company_id, "1000")
    ar = _get_account(db, company_id, "1100")
    return post_balanced_entry(
        db, company_id, f"Payment received for invoice {invoice.invoice_number}",
        "payment", invoice.id, debit_account_id=cash.id, credit_account_id=ar.id, amount=amount, entry_date=datetime.utcnow(),
    )


def post_bill_received(db: Session, company_id: str, bill, expense_gl_account_id: str) -> JournalEntry:
    """Vendor bill received: Debit Expense, Credit Accounts Payable."""
    ap = _get_account(db, company_id, "2000")
    return post_balanced_entry(
        db, company_id, f"Bill {bill.bill_number} received", "bill", bill.id,
        debit_account_id=expense_gl_account_id, credit_account_id=ap.id, amount=bill.total, entry_date=bill.bill_date,
    )


def post_bill_payment(db: Session, company_id: str, bill, amount: Decimal) -> JournalEntry:
    """Company pays a vendor bill: Debit Accounts Payable, Credit Cash."""
    ap = _get_account(db, company_id, "2000")
    cash = _get_account(db, company_id, "1000")
    return post_balanced_entry(
        db, company_id, f"Payment made for bill {bill.bill_number}", "payment", bill.id,
        debit_account_id=ap.id, credit_account_id=cash.id, amount=amount,
    )


def post_expense_approved(db: Session, company_id: str, expense) -> JournalEntry:
    """An approved employee expense becomes a real transaction:
    Debit the expense category's GL account, Credit Cash."""
    cash = _get_account(db, company_id, "1000")
    return post_balanced_entry(
        db, company_id, f"Approved expense: {expense.description or expense.id}",
        "expense", expense.id, debit_account_id=expense.category.gl_account_id,
        credit_account_id=cash.id, amount=expense.amount, created_by=expense.approved_by, entry_date=expense.date,
    )
