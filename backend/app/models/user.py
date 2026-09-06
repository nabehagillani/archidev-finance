import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    FINANCE_MANAGER = "finance_manager"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


# Central permission matrix. Routes check against this rather than
# hardcoding role checks so permissions stay in one place.
ROLE_PERMISSIONS = {
    RoleName.ADMIN: {"*"},
    RoleName.FINANCE_MANAGER: {
        "view_all_financials", "approve_expense", "approve_invoice",
        "generate_report", "view_forecast", "view_ai_insights",
        "manage_budget", "view_audit_log",
    },
    RoleName.ACCOUNTANT: {
        "manage_transaction", "manage_invoice", "manage_expense",
        "reconcile", "generate_report", "manage_customer", "manage_vendor",
    },
    RoleName.VIEWER: {"view_permitted"},
}


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("company_id", "email", name="uq_user_company_email"),)

    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(RoleName), nullable=False, default=RoleName.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")

    def has_permission(self, permission: str) -> bool:
        perms = ROLE_PERMISSIONS.get(self.role, set())
        return "*" in perms or permission in perms
