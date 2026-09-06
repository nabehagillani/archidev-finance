from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import require_permission
from app.services.forecast_service import forecast_metric
from app.models.user import User

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


@router.get("/{metric}")
def get_forecast(
    metric: str, months_forward: int = Query(2, le=6),
    db: Session = Depends(get_db), user: User = Depends(require_permission("view_forecast")),
):
    """metric: revenue | expense | profit. Every forecast point is
    explicitly flagged is_estimate/actual so the frontend can never
    accidentally render a prediction as a real number."""
    return forecast_metric(db, user.company_id, metric, months_forward)
