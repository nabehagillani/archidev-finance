import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Text
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class NotificationSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # null = company-wide
    type = Column(String(50), nullable=False)  # overdue_invoice | low_cash | unusual_expense | ...
    severity = Column(Enum(NotificationSeverity), default=NotificationSeverity.INFO)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
