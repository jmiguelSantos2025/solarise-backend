"""Tests for generation preview and dashboard endpoints."""
from decimal import Decimal

from tests.conftest import auth_header, create_contract, register_user


def _setup(client):
    register_user(client)
    return auth_header(client)


# ── Generation Preview ────────────────────────────────────────────────────────

def test_preview_success(client):
    headers = _setup(client)
    create_contract(client, headers, number="CTRT-001",
                    value_kwh="0.80", percentual_locador="0.30")
    resp = client.post("/generation/preview", json={
        "contract_id": "CTRT-001",
        "generated_energy": "1000.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["saved"] is False
    assert data["loss_factor"] == "0.95"
    # 1000 × 0.80 × 0.95 × 0.30 = 228.00
    assert Decimal(data["value"]) == Decimal("228.00")


def test_preview_contract_not_found(client):
    headers = _setup(client)
    resp = client.post("/generation/preview", json={
        "contract_id": "NONEXISTENT",
        "generated_energy": "500.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers)
    assert resp.status_code == 404


def test_preview_requires_auth(client):
    resp = client.post("/generation/preview", json={
        "contract_id": "CTRT-001",
        "generated_energy": "500.0",
        "date": "2026-03-01T00:00:00",
    })
    assert resp.status_code == 401


def test_preview_energy_must_be_positive(client):
    headers = _setup(client)
    resp = client.post("/generation/preview", json={
        "contract_id": "CTRT-001",
        "generated_energy": "0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers)
    assert resp.status_code == 422


def test_preview_org_scoping_enforced(client):
    """Usuário da Org B não pode ver dados do contrato da Org A."""
    register_user(client, email="a@test.com", name="User A",
                  org_name="OrgA", org_cnpj="11111111000101", org_email="a@org.com")
    headers_a = auth_header(client, email="a@test.com")
    create_contract(client, headers_a, number="SECRET-CONTRACT",
                    value_kwh="0.75", percentual_locador="0.40")

    register_user(client, email="b@test.com", name="User B",
                  org_name="OrgB", org_cnpj="22222222000202", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")

    resp = client.post("/generation/preview", json={
        "contract_id": "SECRET-CONTRACT",
        "generated_energy": "100.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers_b)
    assert resp.status_code == 404


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_no_contract_returns_empty(client):
    headers = _setup(client)
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_month"] is None
    assert data["historical_series"] == []


def test_dashboard_requires_auth(client):
    resp = client.get("/dashboard/landlord")
    assert resp.status_code == 401


def test_dashboard_contract_no_generations_returns_empty(client):
    headers = _setup(client)
    create_contract(client, headers, number="CTRT-001")
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["current_month"] is None


def test_dashboard_aggregates_all_contracts(client, session):
    """O dashboard agrega TODOS os contratos da organização."""
    from datetime import date
    from decimal import Decimal
    from database.models import Contract, EnergyGeneration, Organization, User, calculate_hash
    from app.core.security import create_hash_password

    org = Organization(name="MultiOrg", cnpj="33333333000133", email="multi@org.com")
    session.add(org)
    session.flush()

    user = User(email="multi@test.com", name="Multi User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c1 = Contract(number="C1", organization_id=org.id, start_date=date(2026, 1, 1),
                  value_kwh=Decimal("0.80"), landlord_percentage=Decimal("0.30"), status="active")
    c2 = Contract(number="C2", organization_id=org.id, start_date=date(2026, 1, 1),
                  value_kwh=Decimal("1.50"), landlord_percentage=Decimal("0.50"), status="active")
    session.add(c1)
    session.add(c2)
    session.flush()

    g = EnergyGeneration(contract_id=c2.id, organization_id=org.id,
                         reference_period=date(2026, 4, 1), energy_kwh=Decimal("500"),
                         previous_hash=None, hash_sha256="")
    g.hash_sha256 = calculate_hash(g)
    session.add(g)
    session.commit()

    headers = auth_header(client, email="multi@test.com")
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["current_month"] is not None
    assert data["current_month"]["month"] == "2026-04"
    assert data["current_month"]["kwh"] == 500.0
    # 500 × 1.50 × 0.95 × 0.50 = 356.25
    assert data["current_month"]["value"] == 356.25


def test_dashboard_mes_atual_contains_hash(client, session):
    """current_month deve incluir o hash SHA-256 da última geração do mês."""
    from datetime import date
    from decimal import Decimal
    from database.models import Contract, EnergyGeneration, Organization, User, calculate_hash
    from app.core.security import create_hash_password

    org = Organization(name="HashOrg", cnpj="55500000000155", email="hash@org.com")
    session.add(org)
    session.flush()

    user = User(email="hash@test.com", name="Hash User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c = Contract(number="HASH-CTRT", organization_id=org.id, start_date=date(2026, 1, 1),
                 value_kwh=Decimal("0.85"), landlord_percentage=Decimal("0.30"), status="active")
    session.add(c)
    session.flush()

    g = EnergyGeneration(contract_id=c.id, organization_id=org.id,
                         reference_period=date(2026, 3, 1), energy_kwh=Decimal("38500"),
                         previous_hash=None, hash_sha256="")
    g.hash_sha256 = calculate_hash(g)
    session.add(g)
    session.commit()

    headers = auth_header(client, email="hash@test.com")
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["current_month"] is not None
    assert "hash" in data["current_month"]
    assert data["current_month"]["hash"] == g.hash_sha256
    assert len(data["current_month"]["hash"]) == 64


def test_dashboard_hash_is_last_in_chain(client, session):
    """Com múltiplos registros num mesmo mês, hash retornado deve ser o do último."""
    from datetime import date
    from decimal import Decimal
    from database.models import Contract, EnergyGeneration, Organization, User, calculate_hash
    from app.core.security import create_hash_password

    org = Organization(name="ChainOrg", cnpj="66600000000166", email="chain@org.com")
    session.add(org)
    session.flush()

    user = User(email="chain@test.com", name="Chain User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c = Contract(number="CHAIN-CTRT", organization_id=org.id, start_date=date(2026, 1, 1),
                 value_kwh=Decimal("0.85"), landlord_percentage=Decimal("0.30"), status="active")
    session.add(c)
    session.flush()

    g1 = EnergyGeneration(contract_id=c.id, organization_id=org.id,
                          reference_period=date(2026, 3, 1), energy_kwh=Decimal("10000"),
                          previous_hash=None, hash_sha256="")
    g1.hash_sha256 = calculate_hash(g1)
    session.add(g1)
    session.flush()

    g2 = EnergyGeneration(contract_id=c.id, organization_id=org.id,
                          reference_period=date(2026, 3, 1), energy_kwh=Decimal("5000"),
                          previous_hash=g1.hash_sha256, hash_sha256="")
    g2.hash_sha256 = calculate_hash(g2)
    session.add(g2)
    session.commit()

    headers = auth_header(client, email="chain@test.com")
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["current_month"]["hash"] == g2.hash_sha256


def test_dashboard_serie_historica_max_3_months(client, session):
    """A série histórica deve retornar no máximo os últimos 3 meses."""
    from datetime import date
    from decimal import Decimal
    from database.models import Contract, EnergyGeneration, Organization, User, calculate_hash
    from app.core.security import create_hash_password

    org = Organization(name="SerieOrg", cnpj="44444444000144", email="serie@org.com")
    session.add(org)
    session.flush()

    user = User(email="serie@test.com", name="Serie User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c = Contract(number="S1", organization_id=org.id, start_date=date(2026, 1, 1),
                 value_kwh=Decimal("0.80"), landlord_percentage=Decimal("0.30"), status="active")
    session.add(c)
    session.flush()

    prev_hash = None
    for month in [1, 2, 3, 4, 5]:
        g = EnergyGeneration(contract_id=c.id, organization_id=org.id,
                             reference_period=date(2026, month, 1), energy_kwh=Decimal("100"),
                             previous_hash=prev_hash, hash_sha256="")
        g.hash_sha256 = calculate_hash(g)
        session.add(g)
        session.flush()
        prev_hash = g.hash_sha256
    session.commit()

    headers = auth_header(client, email="serie@test.com")
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["current_month"]["month"] == "2026-05"
    assert len(data["historical_series"]) == 3
    months = [item["month"] for item in data["historical_series"]]
    assert months == ["2026-03", "2026-04", "2026-05"]
