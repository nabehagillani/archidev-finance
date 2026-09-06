from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import require_permission
from app.models.user import User
from app.models.audit import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(db: Session = Depends(get_db), user: User = Depends(require_permission("view_audit_log"))):
    rows = db.query(AuditLog).filter(AuditLog.company_id == user.company_id).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        {"id": r.id, "user_id": r.user_id, "action": r.action, "module": r.module, "record_id": r.record_id,
         "previous_value": r.previous_value, "new_value": r.new_value, "timestamp": r.timestamp}
        for r in rows
    ]
