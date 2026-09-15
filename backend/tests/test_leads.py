from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from auth import AuthContext, get_auth_context
from main import app


class FakeQuery:
    def __init__(self, database: "FakeSupabase", operation: str) -> None:
        self.database = database
        self.operation = operation
        self.filters: dict[str, str] = {}
        self.payload: dict = {}
        self.single = False
        self.select_requested = False

    def insert(self, payload: dict) -> "FakeQuery":
        self.operation = "insert"
        self.payload = payload
        return self

    def select(self, _columns: str = "*") -> "FakeQuery":
        self.select_requested = True
        return self

    def update(self, payload: dict) -> "FakeQuery":
        self.operation = "update"
        self.payload = payload
        return self

    def delete(self) -> "FakeQuery":
        self.operation = "delete"
        return self

    def eq(self, column: str, value: str) -> "FakeQuery":
        self.filters[column] = value
        return self

    def order(self, _column: str, desc: bool = False) -> "FakeQuery":
        return self

    def maybe_single(self) -> "FakeQuery":
        self.single = True
        return self

    def execute(self) -> SimpleNamespace:
        if self.operation == "insert":
            now = datetime.now(UTC).isoformat()
            record = {
                "id": str(uuid4()),
                "status": "new",
                "created_at": now,
                "updated_at": now,
                **self.payload,
            }
            self.database.rows.append(record)
            return SimpleNamespace(data=[record])

        matches = [
            row for row in self.database.rows
            if all(str(row.get(column)) == str(value) for column, value in self.filters.items())
        ]

        if self.operation == "update":
            for row in matches:
                row.update(self.payload)
                row["updated_at"] = datetime.now(UTC).isoformat()
            return SimpleNamespace(data=matches[0] if self.single and matches else matches)

        if self.operation == "delete":
            for row in matches:
                self.database.rows.remove(row)
            return SimpleNamespace(data=matches)

        return SimpleNamespace(data=matches[0] if self.single and matches else matches)


class FakeSupabase:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def table(self, _table_name: str) -> FakeQuery:
        return FakeQuery(self, "select")


fake_supabase = FakeSupabase()


def auth_context(user_id: str = "user-a") -> AuthContext:
    return AuthContext(user_id=user_id, supabase=fake_supabase)  # type: ignore[arg-type]


def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = lambda: auth_context()


def clear_overrides() -> None:
    app.dependency_overrides.clear()
    fake_supabase.rows.clear()


def make_lead(client: TestClient, **overrides: str) -> dict:
    payload = {
        "name": "John Smith",
        "email": "john@example.com",
        "company": "Example Co",
        "message": "I need a website",
        **overrides,
    }
    response = client.post("/leads", json=payload)
    assert response.status_code == 201
    return response.json()


def test_unauthenticated_request_returns_401() -> None:
    client = TestClient(app)
    response = client.get("/leads")
    assert response.status_code == 401


def test_authenticated_user_can_create_and_retrieve_own_leads() -> None:
    override_auth()
    client = TestClient(app)

    created = make_lead(client)
    response = client.get("/leads")

    assert response.status_code == 200
    assert response.json()[0]["id"] == created["id"]
    assert fake_supabase.rows[0]["user_id"] == "user-a"
    clear_overrides()


def test_user_cannot_retrieve_another_users_lead() -> None:
    override_auth()
    client = TestClient(app)
    other_lead = make_lead(client)
    fake_supabase.rows[0]["user_id"] = "user-b"

    response = client.get(f"/leads/{other_lead['id']}")

    assert response.status_code == 404
    clear_overrides()


def test_user_cannot_update_another_users_lead() -> None:
    override_auth()
    client = TestClient(app)
    other_lead = make_lead(client)
    fake_supabase.rows[0]["user_id"] = "user-b"

    response = client.patch(f"/leads/{other_lead['id']}", json={"name": "Changed"})

    assert response.status_code == 404
    assert fake_supabase.rows[0]["name"] == "John Smith"
    clear_overrides()


def test_user_cannot_delete_another_users_lead() -> None:
    override_auth()
    client = TestClient(app)
    other_lead = make_lead(client)
    fake_supabase.rows[0]["user_id"] = "user-b"

    response = client.delete(f"/leads/{other_lead['id']}")

    assert response.status_code == 404
    assert len(fake_supabase.rows) == 1
    clear_overrides()


def test_invalid_lead_data_returns_422() -> None:
    override_auth()
    client = TestClient(app)

    response = client.post("/leads", json={"name": "", "message": ""})

    assert response.status_code == 422
    clear_overrides()
