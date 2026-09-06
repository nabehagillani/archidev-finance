"""
Multi-tenancy root. Every business-data table carries a company_id
foreign key back to Company so one deployment can serve many
customers with fully isolated data.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    industry = Column(String(120))
    base_currency = Column(String(3), default="USD")
    fiscal_year_start_month = Column(String(2), default="01")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
