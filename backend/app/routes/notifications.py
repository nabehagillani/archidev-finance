from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user), unread_only: bool = False):
    q = db.query(Notification).filter(Notification.company_id == user.company_id)
    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712
    rows = q.order_by(Notification.created_at.desc()).limit(100).all()
    return [{"id": r.id, "type": r.type, "severity": r.severity.value, "message": r.message, "is_read": r.is_read, "created_at": r.created_at} for r in rows]


@router.post("/{notification_id}/read")
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.company_id == user.company_id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"status": "ok"}
