import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class InsightSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class FinancialInsight(Base):
    __tablename__ = "financial_insights"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # expense_alert | revenue | cash_flow_risk | payment_risk | cost_saving
    severity = Column(Enum(InsightSeverity), default=InsightSeverity.INFO)
    explanation = Column(Text, nullable=False)
    supporting_data = Column(Text)   # JSON-encoded numbers backing the claim
    recommended_action = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)


class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    metric = Column(String(30), nullable=False)  # revenue | expense | profit | cash_flow
    period_year = Column(String(4), nullable=False)
    period_month = Column(String(2), nullable=False)
    predicted_value = Column(String(30), nullable=False)  # stored as string to keep model light; cast on read
    method = Column(String(50), default="linear_trend")
    generated_at = Column(DateTime, default=datetime.utcnow)
