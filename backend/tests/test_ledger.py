"""
The most important test file in this suite: proves the double-entry
core actually stays balanced through real operations, not just in
isolation. If these fail, the Balance Sheet is lying.
"""
from tests.conftest import signup, auth_headers, get_bank_account_id


def _balance_sheet(client, token):
    return client.get("/api/reports/balance-sheet", headers=auth_headers(token)).json()


def test_books_balance_after_income_and_expense(client):
    auth = signup(client)
    token = auth["access_token"]
    bank_id = get_bank_account_id(client, token)

    r = client.post("/api/transactions", headers=auth_headers(token), json={
        "date": "2026-01-15T00:00:00", "description": "Client payment", "amount": 5000,
        "type": "income", "bank_account_id": bank_id,
    })
    assert r.status_code == 200, r.text

    r = client.post("/api/transactions", headers=auth_headers(token), json={
        "date": "2026-01-16T00:00:00", "description": "Rent", "amount": 1200,
        "type": "expense", "bank_account_id": bank_id,
    })
    assert r.status_code == 200, r.text

    bs = _balance_sheet(client, token)
    assert abs(bs["balances"]) < 0.01, f"Books are out of balance: {bs}"

    kpis = client.get("/api/dashboard/kpis", headers=auth_headers(token)).json()
    assert kpis["total_revenue"] == 5000.0
    assert kpis["total_expenses"] == 1200.0
    assert kpis["net_profit"] == 3800.0
    assert kpis["cash_balance"] == 3800.0


def test_books_balance_after_invoice_and_payment(client):
    auth = signup(client)
    token = auth["access_token"]

    from app.database.session import SessionLocal
    from app.models.parties import Customer

    db = SessionLocal()
    customer = Customer(company_id=auth["company_id"], name="Acme Buyer")
    db.add(customer)
    db.commit()
    db.refresh(customer)

    r = client.post("/api/invoices", headers=auth_headers(token), json={
        "customer_id": customer.id, "invoice_date": "2026-01-01T00:00:00", "due_date": "2026-01-31T00:00:00",
        "items": [{"description": "Consulting", "quantity": 1, "unit_price": 3000, "tax_rate": 0}],
    })
    assert r.status_code == 200, r.text
    invoice_id = r.json()["id"]

    r = client.post(f"/api/invoices/{invoice_id}/send", headers=auth_headers(token))
    assert r.status_code == 200, r.text

    bs = _balance_sheet(client, token)
    assert abs(bs["balances"]) < 0.01
    assert bs["assets"] == 3000.0  # AR

    r = client.post(f"/api/invoices/{invoice_id}/payments", headers=auth_headers(token), params={"amount": 3000})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "paid"

    bs = _balance_sheet(client, token)
    assert abs(bs["balances"]) < 0.01
    assert bs["assets"] == 3000.0  # moved from AR to Cash, total assets unchanged


def test_books_balance_after_bill_and_partial_payment(client):
    auth = signup(client)
    token = auth["access_token"]

    from app.database.session import SessionLocal
    from app.models.parties import Vendor
    from app.models.expense import ExpenseCategory
    from app.models.accounting import Account

    db = SessionLocal()
    vendor = Vendor(company_id=auth["company_id"], name="Power Co")
    db.add(vendor)
    utilities_gl = db.query(Account).filter(Account.company_id == auth["company_id"], Account.code == "6200").first()
    cat = ExpenseCategory(company_id=auth["company_id"], name="Utilities", gl_account_id=utilities_gl.id)
    db.add(cat)
    db.commit()
    db.refresh(vendor)
    db.refresh(cat)

    r = client.post("/api/payables", headers=auth_headers(token), json={
        "vendor_id": vendor.id, "bill_date": "2026-01-01T00:00:00", "due_date": "2026-01-20T00:00:00",
        "total": 800, "category_id": cat.id,
    })
    assert r.status_code == 200, r.text
    bill_id = r.json()["id"]

    bs = _balance_sheet(client, token)
    assert abs(bs["balances"]) < 0.01
    assert bs["liabilities"] == 800.0

    r = client.post(f"/api/payables/{bill_id}/payments", headers=auth_headers(token), params={"amount": 300})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "partially_paid"
    assert r.json()["balance_due"] == 500.0

    bs = _balance_sheet(client, token)
    assert abs(bs["balances"]) < 0.01
    assert bs["liabilities"] == 500.0


def test_overpaying_a_bill_is_rejected(client):
    auth = signup(client)
    token = auth["access_token"]
    from app.database.session import SessionLocal
    from app.models.parties import Vendor
    from app.models.expense import ExpenseCategory
    from app.models.accounting import Account

    db = SessionLocal()
    vendor = Vendor(company_id=auth["company_id"], name="Power Co")
    utilities_gl = db.query(Account).filter(Account.company_id == auth["company_id"], Account.code == "6200").first()
    cat = ExpenseCategory(company_id=auth["company_id"], name="Utilities", gl_account_id=utilities_gl.id)
    db.add_all([vendor, cat])
    db.commit()
    db.refresh(vendor); db.refresh(cat)

    r = client.post("/api/payables", headers=auth_headers(token), json={
        "vendor_id": vendor.id, "bill_date": "2026-01-01T00:00:00", "due_date": "2026-01-20T00:00:00",
        "total": 800, "category_id": cat.id,
    })
    bill_id = r.json()["id"]

    r = client.post(f"/api/payables/{bill_id}/payments", headers=auth_headers(token), params={"amount": 5000})
    assert r.status_code == 400
