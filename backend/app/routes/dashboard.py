from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user
from app.services import dashboard_service
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """All numbers here are computed live from the ledger/AR/AP tables —
    see dashboard_service for the exact query behind each figure."""
    return dashboard_service.get_kpis(db, user.company_id)
