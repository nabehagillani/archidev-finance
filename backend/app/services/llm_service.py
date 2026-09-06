"""
Optional LLM-backed intent classification for the AI Finance Assistant.

This is the extension point the platform spec calls for: "AI should be
designed so an LLM/API can be integrated later without rebuilding the
application." It's wired now, not just documented — set ANTHROPIC_API_KEY
and free-form questions get classified by Claude; leave it unset and the
assistant falls back to the rule-based keyword classifier automatically.

Critically, the LLM is used ONLY to pick which intent applies and pull
out parameters (e.g. an amount mentioned for an affordability check) —
it never sees or reports financial figures itself. The actual numbers
always come from ai_assistant_service's grounded database queries. This
keeps the "never invent an answer" guarantee true regardless of whether
the LLM is enabled.
"""
import json
from app.core.config import settings

INTENT_DESCRIPTIONS = {
    "biggest_expense": "What was the biggest expense category recently?",
    "overdue_customers": "Which customers/invoices are overdue?",
    "average_monthly_expense": "What is the average monthly expense?",
    "profit_change": "Why did profit change / increase / decrease?",
    "cash_flow_forecast": "Predict future cash flow.",
    "affordability_check": "Can we afford a specific planned expense amount?",
    "unknown": "None of the above / unclear.",
}


def is_configured() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def classify_intent_llm(question: str) -> dict | None:
    """
    Returns {"intent": <key>, "params": {...}} or None if the LLM call
    isn't configured or fails for any reason (network, auth, rate limit,
    malformed response) — callers must treat None as "fall back to the
    rule-based classifier", never as an error to surface to the user.
    """
    if not is_configured():
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        intent_list = "\n".join(f"- {k}: {v}" for k, v in INTENT_DESCRIPTIONS.items())

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            system=(
                "You classify a finance question into exactly one intent key from this list:\n"
                f"{intent_list}\n\n"
                "Respond with ONLY a JSON object, no other text: "
                '{"intent": "<key>", "params": {"amount": <number or null>}}. '
                "Only populate params.amount for affordability_check, by extracting any dollar "
                "amount mentioned in the question. Otherwise params.amount is null."
            ),
            messages=[{"role": "user", "content": question}],
        )
        text = response.content[0].text.strip()
        parsed = json.loads(text)
        if parsed.get("intent") not in INTENT_DESCRIPTIONS:
            return None
        return parsed
    except Exception:
        # Any failure (missing package, bad key, network, malformed
        # JSON) silently falls back to the rule-based classifier —
        # the assistant must never go down because the LLM call did.
        return None
