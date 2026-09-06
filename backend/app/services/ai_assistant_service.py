"""
AI Finance Assistant — answers a fixed set of well-defined question
intents by running real queries against the ledger/AR data, so answers
are always grounded in the actual database rather than invented.

Classification: if ANTHROPIC_API_KEY is set (see llm_service.py), a
real LLM call picks which intent applies and extracts parameters from
free-form phrasing. Otherwise a keyword-based classifier does the same
job with less flexibility. Either way, the intent handlers below —
where the actual numbers come from — are identical and never touch the
LLM, so answers stay grounded in real data regardless of which
classifier ran.
"""
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.services import dashboard_service
from app.services import llm_service
from app.models.invoice import Invoice, InvoiceStatus


def _last_month_range():
    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = this_month_start - relativedelta(months=1)
    return last_month_start, this_month_start


# --- Intent handlers: each one is the single source of truth for its
# numbers, regardless of which classifier (LLM or rule-based) routed
# the question here. ---

def _handle_biggest_expense(db, company_id, params):
    start, end = _last_month_range()
    from app.services.insight_service import _category_expense_totals
    totals = _category_expense_totals(db, company_id, start, end)
    data = sorted([{"category": k, "amount": v} for k, v in totals.items()], key=lambda x: -x["amount"])[:5]
    top = data[0]["category"] if data else "N/A"
    return {
        "answer": f"Your biggest expense category last month was {top}.",
        "supporting_numbers": data, "chart_hint": "bar",
        "recommendations": ["Review this category for recurring vs one-off spend."] if data else [],
    }


def _handle_overdue_customers(db, company_id, params):
    now = datetime.utcnow()
    rows = db.query(Invoice).filter(
        Invoice.company_id == company_id, Invoice.due_date < now,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
    ).all()
    data = [{"invoice_number": r.invoice_number, "customer_id": r.customer_id, "balance_due": r.balance_due} for r in rows]
    return {
        "answer": f"{len(data)} invoices are currently overdue." if data else "No invoices are currently overdue.",
        "supporting_numbers": data, "chart_hint": "table",
        "recommendations": ["Prioritize outreach on the largest overdue balances."] if data else [],
    }


def _handle_average_monthly_expense(db, company_id, params):
    start = datetime.utcnow() - relativedelta(months=6)
    total = float(dashboard_service.expense_total(db, company_id, start, datetime.utcnow()))
    avg = total / 6
    return {
        "answer": f"Your average monthly expense over the last 6 months is {avg:,.2f}.",
        "supporting_numbers": {"six_month_total": total, "average": avg}, "chart_hint": "line", "recommendations": [],
    }


def _handle_profit_change(db, company_id, params):
    start, end = _last_month_range()
    prior_start = start - relativedelta(months=1)
    rev_last = float(dashboard_service.revenue_total(db, company_id, start, end))
    rev_prior = float(dashboard_service.revenue_total(db, company_id, prior_start, start))
    exp_last = float(dashboard_service.expense_total(db, company_id, start, end))
    exp_prior = float(dashboard_service.expense_total(db, company_id, prior_start, start))
    profit_last, profit_prior = rev_last - exp_last, rev_prior - exp_prior
    driver = "a revenue decline" if rev_last < rev_prior else "rising expenses" if exp_last > exp_prior else "no clear single driver"
    return {
        "answer": f"Profit changed from {profit_prior:,.2f} to {profit_last:,.2f} month over month, mainly driven by {driver}.",
        "supporting_numbers": {"revenue_last": rev_last, "revenue_prior": rev_prior, "expense_last": exp_last, "expense_prior": exp_prior},
        "chart_hint": "bar", "recommendations": [],
    }


def _handle_cash_flow_forecast(db, company_id, params):
    from app.services.forecast_service import forecast_metric
    fc = forecast_metric(db, company_id, "profit", months_forward=1)
    return {
        "answer": f"Estimated cash flow next month is {fc['forecast'][0]['value']:,.2f} (linear trend estimate — not guaranteed).",
        "supporting_numbers": fc, "chart_hint": "line", "recommendations": [],
    }


def _handle_affordability_check(db, company_id, params):
    planned_amount = params.get("amount") or 0
    cash = float(dashboard_service.cash_balance(db, company_id))
    can_afford = cash - planned_amount > 0
    return {
        "answer": ("Yes, current cash balance covers this expense." if can_afford
                   else "This expense would bring cash balance below zero based on current numbers."),
        "supporting_numbers": {"current_cash": cash, "planned_amount": planned_amount, "resulting_balance": cash - planned_amount},
        "chart_hint": None, "recommendations": [] if can_afford else ["Consider delaying or reducing this expense."],
    }


def _handle_unknown(db, company_id, params):
    return {
        "answer": "I can currently answer questions about biggest expenses, overdue customers, average monthly expense, profit changes, cash flow forecasts, and affordability checks. Try rephrasing your question around one of those.",
        "supporting_numbers": {}, "chart_hint": None, "recommendations": [],
    }


INTENT_HANDLERS = {
    "biggest_expense": _handle_biggest_expense,
    "overdue_customers": _handle_overdue_customers,
    "average_monthly_expense": _handle_average_monthly_expense,
    "profit_change": _handle_profit_change,
    "cash_flow_forecast": _handle_cash_flow_forecast,
    "affordability_check": _handle_affordability_check,
    "unknown": _handle_unknown,
}


def _classify_intent_rule_based(question: str) -> dict:
    q = question.lower()
    if "biggest expense" in q:
        return {"intent": "biggest_expense", "params": {}}
    if "overdue" in q and ("customer" in q or "payment" in q):
        return {"intent": "overdue_customers", "params": {}}
    if "average monthly expense" in q:
        return {"intent": "average_monthly_expense", "params": {}}
    if "profit" in q and ("decrease" in q or "why" in q):
        return {"intent": "profit_change", "params": {}}
    if "cash flow" in q and "predict" in q:
        return {"intent": "cash_flow_forecast", "params": {}}
    if "afford" in q:
        amount_match = re.search(r"[\$]?([\d,]+(?:\.\d+)?)", q)
        amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0
        return {"intent": "affordability_check", "params": {"amount": amount}}
    return {"intent": "unknown", "params": {}}


def answer_question(db: Session, company_id: str, question: str) -> dict:
    classification = llm_service.classify_intent_llm(question) or _classify_intent_rule_based(question)
    handler = INTENT_HANDLERS.get(classification["intent"], _handle_unknown)
    return handler(db, company_id, classification.get("params", {}))
