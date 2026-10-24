import os

# Tests never talk to real services: backend/.env is ignored, get_db is overridden with an
# in-memory fake, and no Gemini key is configured so the assistant uses its rule-based answers.
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_SECRET_KEY"] = "sb_secret_test"
os.environ.pop("GEMINI_API_KEY", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402

Settings.model_config["env_file"] = None

from app.db.client import get_db  # noqa: E402
from app.main import app  # noqa: E402

from .fake_supabase import FakeSupabase  # noqa: E402

PASSWORD = "Password123"


@pytest.fixture
def db() -> FakeSupabase:
    return FakeSupabase()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(client) -> str:
    response = client.post(
        "/api/setup",
        json={"company_name": "Acme", "admin_name": "Ada Admin", "email": "admin@acme.io", "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    # Every day is a working day so attendance tests do not depend on the weekday they run on.
    assert client.patch("/api/company", json={"weekend_days": []}, headers=auth(token)).status_code == 200
    return token


def create_user(client, token: str, email: str, role: str = "employee", salary: int = 30000) -> str:
    response = client.post(
        "/api/employees",
        headers=auth(token),
        json={
            "full_name": email.split("@")[0].title(),
            "email": email,
            "designation": "Staff",
            "join_date": "2020-01-01",
            "monthly_salary": salary,
            "role": role,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    return login.json()["access_token"]
