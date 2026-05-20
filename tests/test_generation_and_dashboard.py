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
        "contract_ID": "CTRT-001",
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
        "contract_ID": "NONEXISTENT",
        "generated_energy": "500.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers)
    assert resp.status_code == 404


def test_preview_requires_auth(client):
    resp = client.post("/generation/preview", json={
        "contract_ID": "CTRT-001",
        "generated_energy": "500.0",
        "date": "2026-03-01T00:00:00",
    })
    assert resp.status_code == 401


def test_preview_energy_must_be_positive(client):
    headers = _setup(client)
    resp = client.post("/generation/preview", json={
        "contract_ID": "CTRT-001",
        "generated_energy": "0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers)
    assert resp.status_code == 422


def test_preview_org_scoping_enforced(client):
    """
    Após a correção, usuário da Org B não pode ver dados do contrato da Org A.
    O filtro organization_id foi adicionado à query de preview.
    """
    register_user(client, email="a@test.com", name="User A",
                  org_name="OrgA", org_cnpj="11111111000101", org_email="a@org.com")
    headers_a = auth_header(client, email="a@test.com")
    create_contract(client, headers_a, number="SECRET-CONTRACT",
                    value_kwh="0.75", percentual_locador="0.40")

    register_user(client, email="b@test.com", name="User B",
                  org_name="OrgB", org_cnpj="22222222000202", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")

    resp = client.post("/generation/preview", json={
        "contract_ID": "SECRET-CONTRACT",
        "generated_energy": "100.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers_b)

    # Com a correção, Org B recebe 404 — não enxerga o contrato de Org A
    assert resp.status_code == 404


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_no_contract_returns_empty(client):
    headers = _setup(client)
    resp = client.get("/dashboard/locador", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mes_atual"] is None
    assert data["serie_historica"] == []


def test_dashboard_requires_auth(client):
    resp = client.get("/dashboard/locador")
    assert resp.status_code == 401


def test_dashboard_contract_no_generations_returns_empty(client):
    headers = _setup(client)
    create_contract(client, headers, number="CTRT-001")
    resp = client.get("/dashboard/locador", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["mes_atual"] is None


def test_dashboard_aggregates_all_contracts(client, session):
    """
    Após a correção, o dashboard agrega TODOS os contratos da organização.
    Org com dois contratos deve retornar dados do contrato com geração,
    mesmo que o outro contrato não tenha registros.
    """
    from datetime import date
    from database.models import Contrato, GeracaoEnergia, Organization, User, calcular_hash
    from app.core.security import create_hash_password

    org = Organization(name="MultiOrg", cnpj="33333333000133", email="multi@org.com")
    session.add(org)
    session.flush()

    user = User(email="multi@test.com", name="Multi User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c1 = Contrato(number="C1", organization_id=org.id, start_date=date(2026, 1, 1),
                  value_kwh=0.80, percentual_locador=0.30, status="active")
    c2 = Contrato(number="C2", organization_id=org.id, start_date=date(2026, 1, 1),
                  value_kwh=1.50, percentual_locador=0.50, status="active")
    session.add(c1)
    session.add(c2)
    session.flush()

    # Geração apenas no segundo contrato
    g = GeracaoEnergia(contrato_id=c2.id, organization_id=org.id,
                       periodo_ref=date(2026, 4, 1), energia_kwh=500.0,
                       hash_anterior=None)
    g.hash_sha256 = calcular_hash(g)
    session.add(g)
    session.commit()

    headers = auth_header(client, email="multi@test.com")
    resp = client.get("/dashboard/locador", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Com a correção, o dashboard encontra c2 e retorna os dados corretamente
    assert data["mes_atual"] is not None
    assert data["mes_atual"]["mes"] == "2026-04"
    assert data["mes_atual"]["kwh"] == 500.0
    # 500 × 1.50 × 0.95 × 0.50 = 356.25
    assert data["mes_atual"]["valor"] == 356.25


def test_dashboard_serie_historica_max_3_months(client, session):
    """A série histórica deve retornar no máximo os últimos 3 meses."""
    from datetime import date
    from database.models import Contrato, GeracaoEnergia, Organization, User, calcular_hash
    from app.core.security import create_hash_password

    org = Organization(name="SerieOrg", cnpj="44444444000144", email="serie@org.com")
    session.add(org)
    session.flush()

    user = User(email="serie@test.com", name="Serie User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c = Contrato(number="S1", organization_id=org.id, start_date=date(2026, 1, 1),
                 value_kwh=0.80, percentual_locador=0.30, status="active")
    session.add(c)
    session.flush()

    prev_hash = None
    for month in [1, 2, 3, 4, 5]:
        g = GeracaoEnergia(contrato_id=c.id, organization_id=org.id,
                           periodo_ref=date(2026, month, 1), energia_kwh=100.0,
                           hash_anterior=prev_hash)
        g.hash_sha256 = calcular_hash(g)
        session.add(g)
        session.flush()
        prev_hash = g.hash_sha256
    session.commit()

    headers = auth_header(client, email="serie@test.com")
    resp = client.get("/dashboard/locador", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["mes_atual"]["mes"] == "2026-05"
    assert len(data["serie_historica"]) == 3
    meses = [item["mes"] for item in data["serie_historica"]]
    assert meses == ["2026-03", "2026-04", "2026-05"]
