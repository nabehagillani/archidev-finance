from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.services.ledger_service import post_expense_approved
from app.routes.insights import _generate_insights_background
from app.services.file_storage_service import save_upload, resolve_path
from app.models.user import User
from app.models.expense import Expense, ExpenseStatus
from app.models.transaction import Transaction, TransactionType
from app.models.audit import AuditLog
from app.schemas.expense import ExpenseCreate, ExpenseOut

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("")
def list_expenses(db: Session = Depends(get_db), user: User = Depends(get_current_user), status: str | None = None):
    q = db.query(Expense).filter(Expense.company_id == user.company_id)
    if status:
        q = q.filter(Expense.status == status)
    rows = q.order_by(Expense.date.desc()).all()
    return [ExpenseOut.model_validate(r).model_dump() for r in rows]


@router.post("", response_model=ExpenseOut)
def submit_expense(payload: ExpenseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Employee submits an expense for approval. Nothing is posted to
    the ledger yet — only an approved expense becomes a real
    transaction (see /approve below), matching the required workflow:
    submit -> review -> approve/reject -> transaction created."""
    exp = Expense(
        company_id=user.company_id, date=payload.date, employee_id=user.id,
        vendor_id=payload.vendor_id, category_id=payload.category_id, amount=payload.amount,
        payment_method=payload.payment_method, description=payload.description,
        status=ExpenseStatus.SUBMITTED,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.post("/{expense_id}/receipt")
def upload_receipt(
    expense_id: str, file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.company_id == user.company_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    storage_key = save_upload(user.company_id, file)
    exp.receipt_url = storage_key
    db.commit()
    return {"receipt_url": storage_key}


@router.get("/{expense_id}/receipt")
def download_receipt(expense_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.company_id == user.company_id).first()
    if not exp or not exp.receipt_url:
        raise HTTPException(status_code=404, detail="No receipt on file for this expense")
    return FileResponse(resolve_path(exp.receipt_url))


@router.post("/{expense_id}/approve", response_model=ExpenseOut)
def approve_expense(
    expense_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
    user: User = Depends(require_permission("approve_expense")),
):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.company_id == user.company_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    if exp.status != ExpenseStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail=f"Expense is already {exp.status.value}")

    previous_status = exp.status.value
    exp.status = ExpenseStatus.APPROVED
    exp.approved_by = user.id
    exp.approved_at = datetime.utcnow()

    from app.models.accounting import Account
    default_bank = db.query(Account).filter(Account.company_id == user.company_id, Account.is_bank_account == True).first()  # noqa: E712
    txn = Transaction(
        company_id=user.company_id, date=exp.date, description=exp.description or f"Expense {exp.id}",
        amount=exp.amount, type=TransactionType.EXPENSE, bank_account_id=default_bank.id, created_by=user.id,
    )
    db.add(txn)
    db.flush()
    entry = post_expense_approved(db, user.company_id, exp)
    txn.journal_entry_id = entry.id
    exp.transaction_id = txn.id

    db.add(AuditLog(
        company_id=user.company_id, user_id=user.id, action=f"approved_expense",
        module="expenses", record_id=exp.id, previous_value=previous_status, new_value="approved",
    ))
    db.commit()
    db.refresh(exp)
    background_tasks.add_task(_generate_insights_background, user.company_id)
    return exp


@router.post("/{expense_id}/reject", response_model=ExpenseOut)
def reject_expense(
    expense_id: str, db: Session = Depends(get_db),
    user: User = Depends(require_permission("approve_expense")),
):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.company_id == user.company_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    previous_status = exp.status.value
    exp.status = ExpenseStatus.REJECTED
    db.add(AuditLog(
        company_id=user.company_id, user_id=user.id, action="rejected_expense",
        module="expenses", record_id=exp.id, previous_value=previous_status, new_value="rejected",
    ))
    db.commit()
    db.refresh(exp)
    return exp
