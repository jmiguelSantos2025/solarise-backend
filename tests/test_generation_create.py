"""Tests for POST /generation/ — create and persist a generation record."""
from tests.conftest import auth_header, create_contract, register_user


def _setup(client, number="CTRT-001", value_kwh="0.80", percentual_locador="0.30"):
    register_user(client)
    headers = auth_header(client)
    create_contract(client, headers, number=number,
                    value_kwh=value_kwh, percentual_locador=percentual_locador)
    return headers


def _post(client, headers, contract_id="CTRT-001",
          energy="1000.0", date="2026-03-01T00:00:00"):
    return client.post("/generation/", json={
        "contract_id": contract_id,
        "generated_energy": energy,
        "date": date,
    }, headers=headers)


def test_create_generation_success(client):
    headers = _setup(client)
    resp = _post(client, headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["ID"]
    assert data["contract_ID"] == "CTRT-001"
    assert data["hash_sha256"]
    assert len(data["hash_sha256"]) == 64
    assert data["previous_hash"] is None
    # 1000 × 0.80 × 0.95 × 0.30 = 228.00
    from decimal import Decimal
    assert Decimal(str(data["value"])) == Decimal("228.00")


def test_create_generation_requires_auth(client):
    register_user(client)
    headers = auth_header(client)
    create_contract(client, headers)

    resp = client.post("/generation/", json={
        "contract_ID": "CTRT-001",
        "generated_energy": "1000.0",
        "date": "2026-03-01T00:00:00",
    })
    assert resp.status_code == 401


def test_create_generation_contract_not_found(client):
    register_user(client)
    headers = auth_header(client)
    resp = _post(client, headers, contract_id="NONEXISTENT")
    assert resp.status_code == 404


def test_create_generation_energy_must_be_positive(client):
    headers = _setup(client)
    resp = _post(client, headers, energy="0")
    assert resp.status_code == 422


def test_create_generation_hash_chain(client):
    """Second record's previous_hash must equal the first record's hash_sha256."""
    headers = _setup(client)

    r1 = _post(client, headers, energy="1000.0", date="2026-03-01T00:00:00")
    assert r1.status_code == 201
    first_hash = r1.json()["hash_sha256"]
    assert r1.json()["previous_hash"] is None

    r2 = _post(client, headers, energy="2000.0", date="2026-04-01T00:00:00")
    assert r2.status_code == 201
    assert r2.json()["previous_hash"] == first_hash


def test_create_generation_org_scoping(client):
    """User from Org B cannot create a generation for Org A's contract."""
    register_user(client, email="a@test.com", name="User A",
                  org_name="OrgA", org_cnpj="11111111000101", org_email="a@org.com")
    headers_a = auth_header(client, email="a@test.com")
    create_contract(client, headers_a, number="CTRT-A")

    register_user(client, email="b@test.com", name="User B",
                  org_name="OrgB", org_cnpj="22222222000202", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")

    resp = _post(client, headers_b, contract_id="CTRT-A")
    assert resp.status_code == 404


def test_dashboard_reflects_saved_generation(client):
    """After POST /generation/, GET /dashboard/locador must return real data."""
    headers = _setup(client, value_kwh="0.80", percentual_locador="0.30")
    _post(client, headers, energy="1000.0", date="2026-03-01T00:00:00")

    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_month"] is not None
    assert data["current_month"]["month"] == "2026-03"
    from decimal import Decimal
    assert Decimal(str(data["current_month"]["value"])) == Decimal("228.00")
