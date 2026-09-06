from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user, require_permission
from app.models.user import User, RoleName
from app.models.tenant import Company
from app.models.accounting import Account
from app.models.parties import Vendor, Customer
from app.models.expense import ExpenseCategory

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/company")
def get_company(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Company).filter(Company.id == user.company_id).first()
    return {"id": c.id, "name": c.name, "base_currency": c.base_currency, "industry": c.industry}


@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Vendor).filter(Vendor.company_id == user.company_id).all()
    return [{"id": v.id, "name": v.name, "email": v.email} for v in rows]


@router.get("/customers")
def list_customers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Customer).filter(Customer.company_id == user.company_id).all()
    return [{"id": c.id, "name": c.name, "email": c.email} for c in rows]


@router.get("/expense-categories")
def list_expense_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ExpenseCategory).filter(ExpenseCategory.company_id == user.company_id).all()
    return [{"id": c.id, "name": c.name, "monthly_limit": float(c.monthly_limit) if c.monthly_limit else None} for c in rows]


@router.get("/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(require_permission("*"))):
    rows = db.query(User).filter(User.company_id == user.company_id).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active} for u in rows]


@router.get("/chart-of-accounts")
def chart_of_accounts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Account).filter(Account.company_id == user.company_id).order_by(Account.code).all()
    return [{"id": a.id, "code": a.code, "name": a.name, "type": a.type.value, "is_bank_account": a.is_bank_account} for a in rows]
