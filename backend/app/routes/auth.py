from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, RoleName
from app.models.tenant import Company
from app.models.accounting import Account, DEFAULT_CHART_OF_ACCOUNTS
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Creates a new tenant (Company), seeds its chart of accounts, and
    registers the first user as Admin. This is how a new customer
    onboards onto the multi-tenant platform."""
    company = Company(name=payload.company_name)
    db.add(company)
    db.flush()

    for code, name, acct_type, is_bank in DEFAULT_CHART_OF_ACCOUNTS:
        db.add(Account(company_id=company.id, code=code, name=name, type=acct_type, is_bank_account=is_bank))

    user = User(
        company_id=company.id, email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name, role=RoleName.ADMIN,
    )
    db.add(user)
    db.commit()

    token = create_access_token({"user_id": user.id, "company_id": company.id, "role": user.role.value})
    return TokenResponse(access_token=token, role=user.role.value, company_id=company.id, full_name=user.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    token = create_access_token({"user_id": user.id, "company_id": user.company_id, "role": user.role.value})
    return TokenResponse(access_token=token, role=user.role.value, company_id=user.company_id, full_name=user.full_name or "")
