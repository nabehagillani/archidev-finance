"""
Confirms the AI Assistant's answers always come from real handler
functions (grounded in the DB) regardless of which classifier routed
the question, and that it degrades gracefully with no LLM configured.
"""
from tests.conftest import signup, auth_headers


def test_assistant_answers_with_no_llm_configured(client):
    """In this test environment ANTHROPIC_API_KEY is never set, so
    every question must route through the rule-based classifier and
    still produce a grounded answer rather than erroring."""
    auth = signup(client)
    token = auth["access_token"]
    r = client.post(
        "/api/ai-assistant/ask", headers=auth_headers(token),
        params={"question": "What were our biggest expenses last month?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body
    assert isinstance(body["supporting_numbers"], list)


def test_assistant_unknown_question_does_not_error(client):
    auth = signup(client)
    token = auth["access_token"]
    r = client.post(
        "/api/ai-assistant/ask", headers=auth_headers(token),
        params={"question": "asdkjaslkdj nonsense question"},
    )
    assert r.status_code == 200
    assert "I can currently answer" in r.json()["answer"]


def test_affordability_check_extracts_amount_and_uses_real_cash_balance(client):
    from tests.conftest import get_bank_account_id
    auth = signup(client)
    token = auth["access_token"]
    bank_id = get_bank_account_id(client, token)

    client.post("/api/transactions", headers=auth_headers(token), json={
        "date": "2026-01-01T00:00:00", "description": "seed cash", "amount": 1000,
        "type": "income", "bank_account_id": bank_id,
    })

    r = client.post(
        "/api/ai-assistant/ask", headers=auth_headers(token),
        params={"question": "Can we afford a $5000 purchase this month?"},
    )
    body = r.json()
    assert body["supporting_numbers"]["current_cash"] == 1000.0
    assert body["supporting_numbers"]["planned_amount"] == 5000.0
    assert "below zero" in body["answer"]
