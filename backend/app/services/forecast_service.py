"""
Lightweight linear-trend forecasting over historical monthly totals.
Deliberately simple (numpy polyfit, degree 1) rather than a black-box
model — with only a few months of real history, a complex model would
overfit and produce false confidence. This lives behind a stable
function signature so a proper time-series model can replace it later
without touching callers.
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from sqlalchemy.orm import Session
from app.services import dashboard_service


def _monthly_series(db: Session, company_id: str, metric: str, months_back: int = 6):
    now = datetime.utcnow()
    series = []
    for i in range(months_back - 1, -1, -1):
        month_start = (now.replace(day=1) - relativedelta(months=i))
        month_end = (month_start + relativedelta(months=1))
        if metric == "revenue":
            val = float(dashboard_service.revenue_total(db, company_id, month_start, month_end))
        elif metric == "expense":
            val = float(dashboard_service.expense_total(db, company_id, month_start, month_end))
        else:
            val = float(dashboard_service.revenue_total(db, company_id, month_start, month_end)) - \
                  float(dashboard_service.expense_total(db, company_id, month_start, month_end))
        series.append({"month": month_start.strftime("%Y-%m"), "value": val, "actual": True})
    return series


def forecast_metric(db: Session, company_id: str, metric: str, months_forward: int = 2, history_months: int = 6):
    history = _monthly_series(db, company_id, metric, history_months)
    y = np.array([p["value"] for p in history])
    x = np.arange(len(y))

    if len(y) < 2 or np.all(y == 0):
        # not enough signal to fit a trend line
        slope, intercept = 0, (y[-1] if len(y) else 0)
    else:
        slope, intercept = np.polyfit(x, y, 1)

    future = []
    now = datetime.utcnow()
    for i in range(1, months_forward + 1):
        month = (now.replace(day=1) + relativedelta(months=i))
        predicted = float(slope * (len(y) - 1 + i) + intercept)
        future.append({"month": month.strftime("%Y-%m"), "value": max(0, round(predicted, 2)), "actual": False})

    return {"metric": metric, "history": history, "forecast": future, "method": "linear_trend", "is_estimate": True}
