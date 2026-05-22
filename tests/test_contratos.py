"""Tests for contract endpoints: create, get, list, update."""
from tests.conftest import auth_header, create_contract, register_user


def _setup(client):
    register_user(client)
    return auth_header(client)


def test_create_contract_success(client):
    headers = _setup(client)
    resp = create_contract(client, headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["number"] == "CTRT-001"
    assert "id" in data
    assert "organization_id" in data


def test_create_contract_requires_auth(client):
    resp = create_contract(client, headers={})
    assert resp.status_code == 401


def test_get_contract_success(client):
    headers = _setup(client)
    created = create_contract(client, headers).json()
    resp = client.get(f"/contratos/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["number"] == "CTRT-001"


def test_get_contract_not_found(client):
    headers = _setup(client)
    resp = client.get("/contratos/00000000-0000-0000-0000-000000000000", headers=headers)
    assert resp.status_code == 404


def test_get_contract_other_org_forbidden(client):
    """Usuário da Org B não pode acessar contrato da Org A."""
    headers_a = _setup(client)
    contract_a = create_contract(client, headers_a).json()

    register_user(client, email="b@test.com", org_name="OrgB",
                  org_cnpj="99999999000199", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")

    resp = client.get(f"/contratos/{contract_a['id']}", headers=headers_b)
    assert resp.status_code == 403


def test_update_contract_success(client):
    headers = _setup(client)
    created = create_contract(client, headers).json()
    resp = client.put(f"/contratos/{created['id']}", json={
        "number": "CTRT-001",
        "description": "Updated description",
        "start_date": "2026-01-01",
        "value_kwh": "0.90",
        "percentual_locador": "0.30",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


def test_update_contract_not_found(client):
    headers = _setup(client)
    resp = client.put("/contratos/00000000-0000-0000-0000-000000000000", json={
        "number": "X", "start_date": "2026-01-01",
        "value_kwh": "0.80", "percentual_locador": "0.30",
    }, headers=headers)
    assert resp.status_code == 404


def test_update_contract_other_org_forbidden(client):
    headers_a = _setup(client)
    contract_a = create_contract(client, headers_a).json()

    register_user(client, email="b@test.com", org_name="OrgB",
                  org_cnpj="99999999000199", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")

    resp = client.put(f"/contratos/{contract_a['id']}", json={
        "number": "CTRT-001", "start_date": "2026-01-01",
        "value_kwh": "0.80", "percentual_locador": "0.30",
    }, headers=headers_b)
    assert resp.status_code == 403


def test_duplicate_contract_number_returns_409(client):
    """Número de contrato duplicado deve retornar 409, não 500."""
    headers = _setup(client)
    create_contract(client, headers, number="SAME-001")
    resp = create_contract(client, headers, number="SAME-001")
    assert resp.status_code == 409


def test_list_contracts_empty(client):
    headers = _setup(client)
    resp = client.get("/contratos/", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_contracts_success(client):
    headers = _setup(client)
    create_contract(client, headers, number="CTRT-001")
    create_contract(client, headers, number="CTRT-002")
    resp = client.get("/contratos/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    numbers = {c["number"] for c in data}
    assert numbers == {"CTRT-001", "CTRT-002"}
    assert "id" in data[0]
    assert "status" in data[0]
    assert "created_at" in data[0]


def test_list_contracts_requires_auth(client):
    resp = client.get("/contratos/")
    assert resp.status_code == 401


def test_list_contracts_org_isolation(client):
    """Org B deve ver apenas seus próprios contratos, nunca os da Org A."""
    headers_a = _setup(client)
    create_contract(client, headers_a, number="ORG-A-CONTRACT")

    register_user(client, email="b@test.com", org_name="OrgB",
                  org_cnpj="99999999000199", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")
    create_contract(client, headers_b, number="ORG-B-CONTRACT")

    resp_a = client.get("/contratos/", headers=headers_a)
    resp_b = client.get("/contratos/", headers=headers_b)

    numbers_a = {c["number"] for c in resp_a.json()}
    numbers_b = {c["number"] for c in resp_b.json()}

    assert numbers_a == {"ORG-A-CONTRACT"}
    assert numbers_b == {"ORG-B-CONTRACT"}


def test_create_contract_invalid_percentual_above_one(client):
    headers = _setup(client)
    resp = create_contract(client, headers, percentual_locador="1.01")
    assert resp.status_code == 422


def test_create_contract_invalid_percentual_zero(client):
    headers = _setup(client)
    resp = create_contract(client, headers, percentual_locador="0")
    assert resp.status_code == 422


def test_create_contract_invalid_value_kwh_zero(client):
    headers = _setup(client)
    resp = create_contract(client, headers, value_kwh="0")
    assert resp.status_code == 422


def test_create_contract_invalid_value_kwh_negative(client):
    headers = _setup(client)
    resp = create_contract(client, headers, value_kwh="-0.50")
    assert resp.status_code == 422


def test_same_number_different_orgs_allowed(client):
    """Duas organizações distintas devem poder usar o mesmo número de contrato."""
    headers_a = _setup(client)
    resp_a = create_contract(client, headers_a, number="SHARED-001")
    assert resp_a.status_code == 201

    register_user(client, email="b@test.com", org_name="OrgB",
                  org_cnpj="99999999000199", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")
    resp_b = create_contract(client, headers_b, number="SHARED-001")
    assert resp_b.status_code == 201


def test_percentual_locador_blocked_after_generation(client, session):
    """Não deve ser possível alterar percentual_locador após registros de geração."""
    from datetime import date
    from database.models import Contrato, GeracaoEnergia, Organization, User, calcular_hash
    from app.core.security import create_hash_password

    org = Organization(name="OrgGen", cnpj="55555555000155", email="gen@org.com")
    session.add(org)
    session.flush()

    user = User(email="gen@test.com", name="Gen User", role="admin",
                organization_id=org.id,
                password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c = Contrato(number="GCTRT-001", organization_id=org.id,
                 start_date=date(2026, 1, 1), value_kwh=0.80,
                 percentual_locador=0.30, status="active")
    session.add(c)
    session.flush()

    g = GeracaoEnergia(contrato_id=c.id, organization_id=org.id,
                       periodo_ref=date(2026, 4, 1), energia_kwh=500.0,
                       hash_anterior=None)
    g.hash_sha256 = calcular_hash(g)
    session.add(g)
    session.commit()

    headers = auth_header(client, email="gen@test.com")
    resp = client.put(f"/contratos/{c.id}", json={
        "number": "GCTRT-001", "start_date": "2026-01-01",
        "value_kwh": "0.80", "percentual_locador": "0.50",  # alterado
    }, headers=headers)
    assert resp.status_code == 409
