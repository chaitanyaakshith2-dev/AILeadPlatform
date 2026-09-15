from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import public as public_module
from fastapi.testclient import TestClient

from main import app


class PublicQuery:
    def __init__(self, database: "PublicDatabase", table_name: str) -> None:
        self.database = database
        self.table_name = table_name
        self.filters: dict[str, str] = {}
        self.payload: dict = {}
        self.single = False

    def select(self, _columns: str = "*") -> "PublicQuery":
        return self

    def eq(self, column: str, value: str) -> "PublicQuery":
        self.filters[column] = value
        return self

    def maybe_single(self) -> "PublicQuery":
        self.single = True
        return self

    def insert(self, payload: dict) -> "PublicQuery":
        self.payload = payload
        return self

    def execute(self) -> SimpleNamespace:
        if self.table_name == "business_settings":
            matches = [
                row for row in self.database.settings
                if all(row.get(key) == value for key, value in self.filters.items())
            ]
            return SimpleNamespace(data=matches[0] if self.single and matches else matches)

        now = datetime.now(UTC).isoformat()
        lead = {"id": str(uuid4()), "status": "new", "created_at": now, "updated_at": now, **self.payload}
        self.database.leads.append(lead)
        return SimpleNamespace(data=[lead])


class PublicDatabase:
    settings = [{"user_id": "user-a", "webhook_token": "a" * 24}]

    def __init__(self) -> None:
        self.leads: list[dict] = []
        self.settings = [*self.settings]

    def table(self, table_name: str) -> PublicQuery:
        return PublicQuery(self, table_name)


def test_public_webhook_associates_lead_with_token_owner(monkeypatch) -> None:
    database = PublicDatabase()
    monkeypatch.setattr(public_module, "get_service_role_client", lambda: database)
    client = TestClient(app)

    response = client.post(
        "/public/leads?token=" + "a" * 24,
        json={"name": "Public Customer", "email": "customer@example.com", "message": "I need help"},
    )

    assert response.status_code == 201
    assert database.leads[0]["user_id"] == "user-a"
    assert response.json()["name"] == "Public Customer"


def test_public_webhook_rejects_unknown_token(monkeypatch) -> None:
    monkeypatch.setattr(public_module, "get_service_role_client", lambda: PublicDatabase())
    client = TestClient(app)

    response = client.post(
        "/public/leads?token=" + "b" * 24,
        json={"name": "Public Customer", "message": "I need help"},
    )

    assert response.status_code == 404
