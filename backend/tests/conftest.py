"""
Shared pytest fixtures. DATABASE_URL is pointed at a throwaway SQLite
file BEFORE any `app.*` module is imported (module-level, at collection
time), since the engine is created once at import time. Each test then
gets a clean set of tables via drop_all/create_all rather than a fresh
process, which is far simpler than trying to reload SQLAlchemy's
metadata mid-run.
"""
import os
import tempfile
import pytest

_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient  # noqa: E402
from app.database.session import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401
import app.main as main_module  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(main_module.app)


def signup(client, company="Test Co", email="owner@test-co.com", password="testpass123"):
    res = client.post("/api/auth/signup", json={
        "company_name": company, "full_name": "Test Owner", "email": email, "password": password,
    })
    assert res.status_code == 200, res.text
    return res.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def get_bank_account_id(client, token):
    res = client.get("/api/settings/chart-of-accounts", headers=auth_headers(token))
    accounts = res.json()
    return next(a["id"] for a in accounts if a["is_bank_account"])
