"""The submit -> approve -> becomes-a-transaction workflow the spec calls for."""
from tests.conftest import signup, auth_headers


def _make_category(client, company_id):
    from app.database.session import SessionLocal
    from app.models.expense import ExpenseCategory
    from app.models.accounting import Account

    db = SessionLocal()
    gl = db.query(Account).filter(Account.company_id == company_id, Account.code == "6400").first()
    cat = ExpenseCategory(company_id=company_id, name="Marketing", gl_account_id=gl.id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat.id


def test_expense_has_no_ledger_impact_until_approved(client):
    auth = signup(client)
    token = auth["access_token"]
    cat_id = _make_category(client, auth["company_id"])

    r = client.post("/api/expenses", headers=auth_headers(token), json={
        "date": "2026-01-05T00:00:00", "category_id": cat_id, "amount": 500, "description": "Trade show flyers",
    })
    assert r.status_code == 200
    expense_id = r.json()["id"]
    assert r.json()["status"] == "submitted"

    kpis = client.get("/api/dashboard/kpis", headers=auth_headers(token)).json()
    assert kpis["total_expenses"] == 0.0, "A submitted-but-unapproved expense must not hit the books"

    r = client.post(f"/api/expenses/{expense_id}/approve", headers=auth_headers(token))
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    kpis = client.get("/api/dashboard/kpis", headers=auth_headers(token)).json()
    assert kpis["total_expenses"] == 500.0, "An approved expense must post to the ledger"


def test_cannot_approve_the_same_expense_twice(client):
    auth = signup(client)
    token = auth["access_token"]
    cat_id = _make_category(client, auth["company_id"])
    r = client.post("/api/expenses", headers=auth_headers(token), json={
        "date": "2026-01-05T00:00:00", "category_id": cat_id, "amount": 200,
    })
    expense_id = r.json()["id"]
    assert client.post(f"/api/expenses/{expense_id}/approve", headers=auth_headers(token)).status_code == 200
    assert client.post(f"/api/expenses/{expense_id}/approve", headers=auth_headers(token)).status_code == 400


def test_rejected_expense_never_posts(client):
    auth = signup(client)
    token = auth["access_token"]
    cat_id = _make_category(client, auth["company_id"])
    r = client.post("/api/expenses", headers=auth_headers(token), json={
        "date": "2026-01-05T00:00:00", "category_id": cat_id, "amount": 750,
    })
    expense_id = r.json()["id"]
    assert client.post(f"/api/expenses/{expense_id}/reject", headers=auth_headers(token)).status_code == 200

    kpis = client.get("/api/dashboard/kpis", headers=auth_headers(token)).json()
    assert kpis["total_expenses"] == 0.0
