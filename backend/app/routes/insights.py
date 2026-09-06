import json
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db, SessionLocal
from app.services.auth_service import require_permission
from app.services.insight_service import generate_insights
from app.models.insight import FinancialInsight
from app.models.user import User

router = APIRouter(prefix="/api/insights", tags=["insights"])


def _generate_insights_background(company_id: str):
    """Background-task entrypoint: opens its own DB session rather than
    reusing the request's (which is closed by the time this runs), so
    insight regeneration never blocks the triggering request — useful
    for imports/approvals where the caller shouldn't wait on analysis."""
    db = SessionLocal()
    try:
        generate_insights(db, company_id)
    finally:
        db.close()


@router.post("/generate")
def refresh_insights(
    background_tasks: BackgroundTasks, db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_ai_insights")),
):
    """Re-runs all insight rules against current data. Called automatically
    after new data lands (import, reconciliation, approval) per the
    automation flow in the spec, and can also be triggered manually.
    Runs in the background so the caller isn't blocked on analysis."""
    background_tasks.add_task(_generate_insights_background, user.company_id)
    return {"status": "queued"}


@router.get("")
def list_insights(db: Session = Depends(get_db), user: User = Depends(require_permission("view_ai_insights"))):
    rows = db.query(FinancialInsight).filter(FinancialInsight.company_id == user.company_id).order_by(FinancialInsight.generated_at.desc()).limit(50).all()
    return [
        {
            "id": r.id, "category": r.category, "severity": r.severity.value, "explanation": r.explanation,
            "supporting_data": json.loads(r.supporting_data) if r.supporting_data else {},
            "recommended_action": r.recommended_action, "generated_at": r.generated_at,
        } for r in rows
    ]
