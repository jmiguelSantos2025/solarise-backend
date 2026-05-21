import os

# Must be set before any project imports
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "testsecretkey12345678901234567890xx"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_HOURS"] = "24"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["APP_ENV"] = "production"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from database.database import get_session

_TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate all tables before each test and drop them after."""
    SQLModel.metadata.create_all(_TEST_ENGINE)
    yield
    SQLModel.metadata.drop_all(_TEST_ENGINE)


@pytest.fixture(name="client")
def client_fixture():
    def override_get_session():
        with Session(_TEST_ENGINE) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="session")
def session_fixture():
    with Session(_TEST_ENGINE) as session:
        yield session


# ─── Helpers ────────────────────────────────────────────────────────────────

def register_user(client, email="user@test.com", password="Password1@", name="Test User",
                  role="admin", org_name="TestOrg", org_cnpj="12345678000100",
                  org_email="org@test.com"):
    return client.post("/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "org_name": org_name,
        "org_cnpj": org_cnpj,
        "org_email": org_email,
    })


def login_user(client, email="user@test.com", password="Password1@"):
    return client.post("/auth/login", data={"username": email, "password": password})


def auth_header(client, email="user@test.com", password="Password1@"):
    resp = login_user(client, email, password)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_contract(client, headers, number="CTRT-001", value_kwh="0.80",
                    percentual_locador="0.30", start_date="2026-01-01"):
    return client.post("/contratos/", json={
        "number": number,
        "description": "Test contract",
        "start_date": start_date,
        "value_kwh": value_kwh,
        "percentual_locador": percentual_locador,
    }, headers=headers)
