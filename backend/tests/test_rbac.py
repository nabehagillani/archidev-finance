"""
Proves permission checks are actually enforced server-side, not just
hidden in the UI. A Viewer or a plain signed-up user must be rejected
by the API itself when they lack a permission.
"""
from tests.conftest import signup, auth_headers


def _create_viewer(client, admin_token, company_id):
    from app.database.session import SessionLocal
    from app.models.user import User, RoleName
    from app.core.security import hash_password

    db = SessionLocal()
    viewer = User(
        company_id=company_id, email="viewer@test-co.com",
        hashed_password=hash_password("viewpass123"), full_name="A Viewer", role=RoleName.VIEWER,
    )
    db.add(viewer)
    db.commit()

    r = client.post("/api/auth/login", json={"email": "viewer@test-co.com", "password": "viewpass123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_admin_can_do_everything(client):
    auth = signup(client)
    token = auth["access_token"]
    from tests.conftest import get_bank_account_id
    bank_id = get_bank_account_id(client, token)
    r = client.post("/api/transactions", headers=auth_headers(token), json={
        "date": "2026-01-01T00:00:00", "description": "test", "amount": 100,
        "type": "income", "bank_account_id": bank_id,
    })
    assert r.status_code == 200


def test_viewer_cannot_create_transactions(client):
    auth = signup(client)
    viewer_token = _create_viewer(client, auth["access_token"], auth["company_id"])
    from tests.conftest import get_bank_account_id
    bank_id = get_bank_account_id(client, auth["access_token"])

    r = client.post("/api/transactions", headers=auth_headers(viewer_token), json={
        "date": "2026-01-01T00:00:00", "description": "test", "amount": 100,
        "type": "income", "bank_account_id": bank_id,
    })
    assert r.status_code == 403


def test_viewer_cannot_approve_expenses(client):
    auth = signup(client)
    viewer_token = _create_viewer(client, auth["access_token"], auth["company_id"])
    r = client.post("/api/expenses/some-fake-id/approve", headers=auth_headers(viewer_token))
    assert r.status_code == 403  # denied for lacking the permission, before it even checks existence


def test_viewer_can_still_read_dashboard(client):
    auth = signup(client)
    viewer_token = _create_viewer(client, auth["access_token"], auth["company_id"])
    r = client.get("/api/dashboard/kpis", headers=auth_headers(viewer_token))
    assert r.status_code == 200


def test_unauthenticated_request_is_rejected(client):
    r = client.get("/api/dashboard/kpis")
    assert r.status_code == 401


def test_users_from_different_companies_cannot_see_each_others_data(client):
    auth_a = signup(client, company="Company A", email="a@company-a.com")
    auth_b = signup(client, company="Company B", email="b@company-b.com")
    from tests.conftest import get_bank_account_id

    bank_a = get_bank_account_id(client, auth_a["access_token"])
    client.post("/api/transactions", headers=auth_headers(auth_a["access_token"]), json={
        "date": "2026-01-01T00:00:00", "description": "Company A income", "amount": 9999,
        "type": "income", "bank_account_id": bank_a,
    })

    kpis_b = client.get("/api/dashboard/kpis", headers=auth_headers(auth_b["access_token"])).json()
    assert kpis_b["total_revenue"] == 0.0, "Company B should not see Company A's revenue"
