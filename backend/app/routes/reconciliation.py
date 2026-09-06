import io
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.models.user import User
from app.models.bank import BankTransaction, Reconciliation, MatchStatus
from app.models.transaction import Transaction
from app.models.accounting import Account

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


@router.post("/upload")
def upload_bank_statement(
    file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_permission("reconcile")),
):
    """
    Parses an uploaded bank statement, then matches each line against
    internal transactions by (amount, date within 3 days). Flags exact
    duplicates (same amount/date/description already staged) and
    amount mismatches (same date+description, different amount).
    """
    raw = file.file.read()
    filename = (file.filename or "").lower()
    df = pd.read_csv(io.BytesIO(raw)) if filename.endswith(".csv") else pd.read_excel(io.BytesIO(raw))

    col_map = {c.lower().strip(): c for c in df.columns}
    date_col = col_map.get("date")
    desc_col = col_map.get("description") or col_map.get("memo")
    amount_col = col_map.get("amount")
    if not (date_col and desc_col and amount_col):
        raise HTTPException(status_code=400, detail=f"Could not detect required columns. Found: {list(df.columns)}")

    default_bank = db.query(Account).filter(Account.company_id == user.company_id, Account.is_bank_account == True).first()  # noqa: E712

    matched = duplicate = unmatched = 0
    for _, row in df.iterrows():
        date = pd.to_datetime(row[date_col])
        amount = float(row[amount_col])
        description = str(row[desc_col])

        already_staged = db.query(BankTransaction).filter(
            BankTransaction.company_id == user.company_id, BankTransaction.date == date,
            BankTransaction.amount == amount, BankTransaction.description == description,
        ).first()
        if already_staged:
            status = MatchStatus.DUPLICATE
            duplicate += 1
        else:
            candidate = db.query(Transaction).filter(
                Transaction.company_id == user.company_id,
                Transaction.amount == abs(amount),
                Transaction.date >= date - pd.Timedelta(days=3),
                Transaction.date <= date + pd.Timedelta(days=3),
            ).first()
            if candidate:
                status = MatchStatus.MATCHED
                matched += 1
            else:
                status = MatchStatus.UNMATCHED
                unmatched += 1

        db.add(BankTransaction(
            company_id=user.company_id, bank_account_id=default_bank.id, date=date,
            description=description, amount=amount, match_status=status,
            matched_transaction_id=candidate.id if status == MatchStatus.MATCHED else None,
        ))

    total = matched + duplicate + unmatched
    match_rate = round((matched / total) * 100, 1) if total else 0.0
    recon = Reconciliation(
        company_id=user.company_id, bank_account_id=default_bank.id, total_bank_lines=total,
        matched_count=matched, unmatched_count=unmatched, duplicate_count=duplicate, match_rate_pct=match_rate,
    )
    db.add(recon)
    db.commit()

    return {
        "total_lines": total, "matched": matched, "unmatched": unmatched,
        "duplicates": duplicate, "match_rate_pct": match_rate,
    }
