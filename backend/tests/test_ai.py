import leads as leads_module
from ai import LeadAnalysis
from fastapi.testclient import TestClient

from main import app
from test_leads import clear_overrides, fake_supabase, override_auth


def test_authenticated_user_can_analyze_own_lead(monkeypatch) -> None:
    override_auth()
    client = TestClient(app)
    created = client.post(
        "/leads",
        json={"name": "Jane Doe", "message": "We need an ecommerce site"},
    )
    lead_id = created.json()["id"]
    expected = LeadAnalysis(
        lead_score=87,
        business_type="Retail",
        budget="$10,000",
        timeline="This quarter",
        requirements=["Ecommerce site"],
        priority="HIGH",
        reasoning="The lead has a clear project need and near-term timeline.",
    )
    monkeypatch.setattr(leads_module, "analyze_lead_with_ai", lambda _message: expected)

    response = client.post(f"/leads/{lead_id}/analyze")

    assert response.status_code == 200
    assert response.json()["analysis"]["lead_score"] == 87
    assert fake_supabase.rows[0]["analysis"]["priority"] == "HIGH"
    clear_overrides()


def test_user_cannot_analyze_another_users_lead(monkeypatch) -> None:
    override_auth()
    client = TestClient(app)
    created = client.post(
        "/leads",
        json={"name": "Jane Doe", "message": "We need an ecommerce site"},
    )
    fake_supabase.rows[0]["user_id"] = "user-b"
    monkeypatch.setattr(
        leads_module,
        "analyze_lead_with_ai",
        lambda _message: (_ for _ in ()).throw(AssertionError("AI should not be called")),
    )

    response = client.post(f"/leads/{created.json()['id']}/analyze")

    assert response.status_code == 404
    clear_overrides()


def test_analysis_model_rejects_invalid_priority() -> None:
    try:
        LeadAnalysis(
            lead_score=50,
            business_type="Other",
            requirements=[],
            priority="URGENT",
            reasoning="No reasoning",
        )
    except ValueError:
        return
    raise AssertionError("Invalid priority should be rejected")


def test_authenticated_user_can_generate_followup_reply(monkeypatch) -> None:
    override_auth()
    client = TestClient(app)
    created = client.post(
        "/leads",
        json={"name": "Jane Doe", "message": "We need an ecommerce site"},
    )
    fake_supabase.rows[0]["analysis"] = {
        "lead_score": 87,
        "business_type": "Retail",
        "budget": "$10,000",
        "timeline": "This quarter",
        "requirements": ["Ecommerce site"],
        "priority": "HIGH",
        "reasoning": "Clear project need.",
    }
    monkeypatch.setattr(
        leads_module,
        "generate_followup_reply",
        lambda message, analysis, settings: "Thanks for reaching out. I would be happy to discuss your ecommerce project.",
    )

    response = client.post(f"/leads/{created.json()['id']}/generate-reply")

    assert response.status_code == 200
    assert response.json() == {
        "suggested_reply": "Thanks for reaching out. I would be happy to discuss your ecommerce project.",
    }
    clear_overrides()


def test_reply_requires_existing_analysis() -> None:
    override_auth()
    client = TestClient(app)
    created = client.post(
        "/leads",
        json={"name": "Jane Doe", "message": "We need an ecommerce site"},
    )

    response = client.post(f"/leads/{created.json()['id']}/generate-reply")

    assert response.status_code == 400
    clear_overrides()
