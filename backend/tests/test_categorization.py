"""
Proves the categorization engine actually "learns" from corrections
per the spec requirement — both the keyword fallback and, once enough
history exists, the ML classifier.
"""
from datetime import datetime
from tests.conftest import signup, auth_headers, get_bank_account_id


def _make_category(client, company_id, name, code):
    from app.database.session import SessionLocal
    from app.models.transaction import TransactionCategory
    from app.models.accounting import Account

    db = SessionLocal()
    gl = db.query(Account).filter(Account.company_id == company_id, Account.code == code).first()
    cat = TransactionCategory(company_id=company_id, name=name, gl_account_id=gl.id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def test_correcting_a_category_updates_keyword_rules(client):
    auth = signup(client)
    token = auth["access_token"]
    bank_id = get_bank_account_id(client, token)
    cat = _make_category(client, auth["company_id"], "Software/Subscription", "6300")

    r = client.post("/api/transactions", headers=auth_headers(token), json={
        "date": "2026-01-01T00:00:00", "description": "Zoomly video calls", "amount": 40,
        "type": "expense", "bank_account_id": bank_id,
    })
    txn_id = r.json()["id"]

    r = client.patch(f"/api/transactions/{txn_id}/category", headers=auth_headers(token), params={"category_id": cat.id})
    assert r.status_code == 200

    from app.database.session import SessionLocal
    from app.models.transaction import TransactionCategory
    db = SessionLocal()
    refreshed = db.query(TransactionCategory).filter(TransactionCategory.id == cat.id).first()
    assert "zoomly" in refreshed.keyword_rules.lower()

    # A second, unrelated transaction from the same vendor should now auto-categorize.
    from app.services.categorization_service import suggest_category
    suggestion = suggest_category(db, auth["company_id"], "Zoomly video calls - monthly")
    assert suggestion is not None
    assert suggestion.id == cat.id


def test_correcting_unknown_category_is_rejected(client):
    auth = signup(client)
    token = auth["access_token"]
    bank_id = get_bank_account_id(client, token)
    r = client.post("/api/transactions", headers=auth_headers(token), json={
        "date": "2026-01-01T00:00:00", "description": "Something", "amount": 40,
        "type": "expense", "bank_account_id": bank_id,
    })
    txn_id = r.json()["id"]
    r = client.patch(f"/api/transactions/{txn_id}/category", headers=auth_headers(token), params={"category_id": "does-not-exist"})
    assert r.status_code == 400


def test_ml_categorization_activates_after_enough_history(client):
    """Below the labeled-example threshold, the ML model must not
    activate (returns None) so keyword rules keep doing the work."""
    auth = signup(client)
    company_id = auth["company_id"]
    cat_a = _make_category(client, company_id, "Marketing", "6400")
    cat_b = _make_category(client, company_id, "Utilities", "6200")

    from app.database.session import SessionLocal
    from app.models.transaction import Transaction, TransactionType
    from app.services import ml_categorization_service

    db = SessionLocal()
    # Below MIN_EXAMPLES_PER_CATEGORY (5) — must not train yet.
    for i in range(3):
        db.add(Transaction(
            company_id=company_id, date=datetime(2026, 1, 1), description=f"Facebook ads campaign {i}",
            amount=100, type=TransactionType.EXPENSE, category_id=cat_a.id, bank_account_id=cat_a.gl_account_id,
        ))
    db.commit()
    assert ml_categorization_service.train(db, company_id) is False

    # Cross the threshold for two categories -> should train successfully.
    for i in range(3, 6):
        db.add(Transaction(
            company_id=company_id, date=datetime(2026, 1, 1), description=f"Facebook ads campaign {i}",
            amount=100, type=TransactionType.EXPENSE, category_id=cat_a.id, bank_account_id=cat_a.gl_account_id,
        ))
    for i in range(6):
        db.add(Transaction(
            company_id=company_id, date=datetime(2026, 1, 1), description=f"Electricity bill payment {i}",
            amount=80, type=TransactionType.EXPENSE, category_id=cat_b.id, bank_account_id=cat_b.gl_account_id,
        ))
    db.commit()
    assert ml_categorization_service.train(db, company_id) is True
