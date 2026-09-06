"""
Rule-based auto-categorization for imported transactions.

Deliberately a simple, explainable keyword-matching engine for v1 rather
than an opaque ML classifier — finance users need to see *why* something
was categorized a certain way, and corrections need to immediately and
visibly improve future matches. Each correction appends the transaction's
key description term to that category's keyword_rules, so the system
"learns" in a fully auditable way. A statistical/ML classifier
(scikit-learn) can be swapped in later behind the same
`suggest_category()` interface without touching callers.
"""
import re
from sqlalchemy.orm import Session
from app.models.transaction import TransactionCategory
from app.services import ml_categorization_service

DEFAULT_KEYWORD_MAP = {
    "Software/Subscription": ["netflix", "spotify", "subscription", "saas", "software", "aws", "github"],
    "Rent": ["rent", "lease"],
    "Utilities": ["electricity", "utility", "utilities", "water bill", "gas bill"],
    "Revenue": ["client payment", "invoice payment", "customer payment", "sales"],
    "Marketing": ["ads", "advertising", "marketing", "facebook ads", "google ads"],
    "Salaries & Wages": ["payroll", "salary", "wages"],
    "Office Supplies": ["office supplies", "stationery"],
}


def suggest_category(db: Session, company_id: str, description: str) -> TransactionCategory | None:
    """Tries the ML classifier first (once a company has enough labeled
    history — see ml_categorization_service for the threshold), then
    falls back to keyword matching. A brand-new company with no history
    yet gets pure keyword matching, which is exactly the behavior it
    had before ML was ever added."""
    ml_result = ml_categorization_service.predict(db, company_id, description)
    if ml_result:
        return ml_result

    desc = description.lower()
    categories = db.query(TransactionCategory).filter(TransactionCategory.company_id == company_id).all()
    for cat in categories:
        keywords = [k.strip().lower() for k in (cat.keyword_rules or "").split(",") if k.strip()]
        if any(re.search(re.escape(kw), desc) for kw in keywords):
            return cat
    return None


def learn_from_correction(db: Session, category: TransactionCategory, description: str):
    """Called when a user manually corrects a transaction's category.
    Appends a distinguishing token from the description to that
    category's keyword rules so the same vendor auto-categorizes
    correctly next time, and invalidates the cached ML model for this
    company so the next categorization attempt retrains on the new,
    corrected label."""
    token = description.lower().split()[0] if description else None
    if token:
        existing = set((category.keyword_rules or "").split(","))
        existing.discard("")
        existing.add(token)
        category.keyword_rules = ",".join(sorted(existing))
        db.add(category)
    ml_categorization_service.invalidate(category.company_id)
