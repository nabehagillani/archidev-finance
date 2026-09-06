import io
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.services import categorization_service
from app.services.ledger_service import post_transaction
from app.routes.insights import _generate_insights_background
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionCategory
from app.models.audit import AuditLog
from app.schemas.transaction import TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.patch("/{transaction_id}/category")
def correct_category(
    transaction_id: str, category_id: str, db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_transaction")),
):
    """Lets a finance employee correct an auto-assigned category. This
    is what makes the categorization engine actually 'learn' — both the
    keyword rules and the ML model (once enough history exists) improve
    from this correction, per categorization_service.learn_from_correction."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.company_id == user.company_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    category = db.query(TransactionCategory).filter(
        TransactionCategory.id == category_id, TransactionCategory.company_id == user.company_id,
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="Unknown category")

    previous_category_id = txn.category_id
    txn.category_id = category_id
    categorization_service.learn_from_correction(db, category, txn.description)

    db.add(AuditLog(
        company_id=user.company_id, user_id=user.id, action="corrected_transaction_category",
        module="transactions", record_id=txn.id, previous_value=previous_category_id, new_value=category_id,
    ))
    db.commit()
    return {"status": "updated", "category_id": category_id}


@router.get("")
def list_transactions(
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
    type: str | None = None, search: str | None = None,
    page: int = 1, page_size: int = 25,
):
    q = db.query(Transaction).filter(Transaction.company_id == user.company_id)
    if type:
        q = q.filter(Transaction.type == type)
    if search:
        q = q.filter(Transaction.description.ilike(f"%{search}%"))
    total = q.count()
    rows = q.order_by(Transaction.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [TransactionOut.model_validate(r).model_dump() for r in rows],
    }


@router.post("", response_model=TransactionOut)
def create_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_transaction")),
):
    txn = Transaction(
        company_id=user.company_id, date=payload.date, description=payload.description,
        amount=payload.amount, type=payload.type, category_id=payload.category_id,
        bank_account_id=payload.bank_account_id, payment_method=payload.payment_method,
        reference=payload.reference, notes=payload.notes, created_by=user.id,
    )
    db.add(txn)
    db.flush()

    if txn.type != TransactionType.TRANSFER:
        entry = post_transaction(db, user.company_id, txn)
        txn.journal_entry_id = entry.id

    db.add(AuditLog(
        company_id=user.company_id, user_id=user.id, action="created_transaction",
        module="transactions", record_id=txn.id, new_value=payload.model_dump_json(),
    ))
    db.commit()
    db.refresh(txn)
    return txn


@router.post("/import")
def import_transactions(
    background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_transaction")),
):
    """
    Accepts CSV or Excel bank/transaction exports. Column names are
    matched loosely (case-insensitive, common synonyms) so the user
    doesn't need to reformat their export first, then each row is
    auto-categorized via categorization_service and posted to the
    ledger like any manually-entered transaction.
    """
    raw = file.file.read()
    filename = (file.filename or "").lower()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        else:
            df = pd.read_excel(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    col_map = {c.lower().strip(): c for c in df.columns}

    def find_col(*candidates):
        for cand in candidates:
            if cand in col_map:
                return col_map[cand]
        return None

    date_col = find_col("date", "transaction date", "posted date")
    desc_col = find_col("description", "memo", "narrative", "details")
    amount_col = find_col("amount", "value", "debit/credit")

    if not (date_col and desc_col and amount_col):
        raise HTTPException(
            status_code=400,
            detail=f"Could not detect required columns. Found: {list(df.columns)}. "
                   f"Need a date, description, and amount column.",
        )

    bank_account = db.query(Transaction).first()  # noqa: placeholder lookup pattern
    from app.models.accounting import Account
    default_bank = db.query(Account).filter(Account.company_id == user.company_id, Account.is_bank_account == True).first()  # noqa: E712
    if not default_bank:
        raise HTTPException(status_code=400, detail="No bank account configured for this company")

    created, errors = 0, []
    for i, row in df.iterrows():
        try:
            amount = float(row[amount_col])
            description = str(row[desc_col])
            txn_type = TransactionType.INCOME if amount >= 0 else TransactionType.EXPENSE
            category = categorization_service.suggest_category(db, user.company_id, description)

            txn = Transaction(
                company_id=user.company_id, date=pd.to_datetime(row[date_col]),
                description=description, amount=abs(amount), type=txn_type,
                category_id=category.id if category else None,
                bank_account_id=default_bank.id, created_by=user.id,
            )
            db.add(txn)
            db.flush()
            entry = post_transaction(db, user.company_id, txn)
            txn.journal_entry_id = entry.id
            created += 1
        except Exception as e:
            errors.append({"row": int(i), "error": str(e)})

    db.add(AuditLog(
        company_id=user.company_id, user_id=user.id, action="imported_transactions",
        module="transactions", new_value=f"{created} rows imported, {len(errors)} errors",
    ))
    db.commit()
    background_tasks.add_task(_generate_insights_background, user.company_id)
    return {"rows_processed": len(df), "created": created, "errors": errors}
