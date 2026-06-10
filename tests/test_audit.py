"""Tests for POST /generation/{contract_id}/audit — hash chain integrity endpoint."""
import uuid
from decimal import Decimal

import pytest

from tests.conftest import auth_header, create_contract, register_user


def _setup_with_generations(client, n_generations=3):
    """Register user, create contract, create n generations. Returns (headers, contract_uuid)."""
    register_user(client)
    headers = auth_header(client)
    create_contract(client, headers, number="AUDIT-001", value_kwh="0.85", percentual_locador="0.30")

    contract_uuid = client.get("/contracts/", headers=headers).json()[0]["id"]

    months = [
        ("2026-01-01T00:00:00", "36200"),
        ("2026-02-01T00:00:00", "34850"),
        ("2026-03-01T00:00:00", "38500"),
    ]
    for date_str, energy in months[:n_generations]:
        r = client.post("/generation/", json={
            "contract_id": "AUDIT-001",
            "generated_energy": energy,
            "date": date_str,
        }, headers=headers)
        assert r.status_code == 201
    return headers, contract_uuid


def test_audit_valid_chain(client):
    """A cadeia de hashes de 3 gerações deve ser completamente válida."""
    headers, contract_uuid = _setup_with_generations(client, n_generations=3)

    resp = client.post(f"/generation/{contract_uuid}/audit", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert data["chain_valid"] is True
    assert data["total_records"] == 3
    assert data["valid_records"] == 3
    assert data["invalid_records"] == 0
    assert len(data["details"]) == 3
    for entry in data["details"]:
        assert entry["valid"] is True
        assert "reason" in entry
        assert "id" in entry


def test_audit_requires_auth(client):
    """Endpoint de auditoria deve exigir autenticação."""
    _setup_with_generations(client, n_generations=1)
    random_contract_id = uuid.uuid4()
    resp = client.post(f"/generation/{random_contract_id}/audit")
    assert resp.status_code == 401


def test_audit_no_records_returns_404(client):
    """Auditoria de contrato sem gerações deve retornar 404."""
    register_user(client)
    headers = auth_header(client)
    create_contract(client, headers, number="EMPTY-001")
    contract_uuid = client.get("/contracts/", headers=headers).json()[0]["id"]

    resp = client.post(f"/generation/{contract_uuid}/audit", headers=headers)
    assert resp.status_code == 404


def test_audit_nonexistent_contract_returns_404(client):
    """Auditoria de contract_id inexistente deve retornar 404."""
    register_user(client)
    headers = auth_header(client)
    fake_id = uuid.uuid4()
    resp = client.post(f"/generation/{fake_id}/audit", headers=headers)
    assert resp.status_code == 404


def test_audit_org_isolation(client):
    """Usuário da Org B não pode auditar contratos da Org A."""
    register_user(client, email="a@test.com", name="User A",
                  org_name="OrgA", org_cnpj="11111111000101", org_email="a@org.com")
    headers_a = auth_header(client, email="a@test.com")
    create_contract(client, headers_a, number="SECRET-AUDIT")
    client.post("/generation/", json={
        "contract_id": "SECRET-AUDIT",
        "generated_energy": "1000",
        "date": "2026-03-01T00:00:00",
    }, headers=headers_a)
    contract_uuid_a = client.get("/contracts/", headers=headers_a).json()[0]["id"]

    register_user(client, email="b@test.com", name="User B",
                  org_name="OrgB", org_cnpj="22222222000202", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")

    resp = client.post(f"/generation/{contract_uuid_a}/audit", headers=headers_b)
    assert resp.status_code == 404, (
        f"Isolamento falhou: Org B auditou contrato da Org A (status {resp.status_code})"
    )


def test_audit_invalid_uuid_returns_422(client):
    """UUID inválido no path deve retornar 422."""
    register_user(client)
    headers = auth_header(client)
    resp = client.post("/generation/not-a-uuid/audit", headers=headers)
    assert resp.status_code == 422


def test_audit_single_record(client):
    """Auditoria com apenas 1 registro deve funcionar (sem previous_hash)."""
    register_user(client)
    headers = auth_header(client)
    create_contract(client, headers, number="SINGLE-001")
    client.post("/generation/", json={
        "contract_id": "SINGLE-001",
        "generated_energy": "500",
        "date": "2026-01-01T00:00:00",
    }, headers=headers)
    contract_uuid = client.get("/contracts/", headers=headers).json()[0]["id"]

    resp = client.post(f"/generation/{contract_uuid}/audit", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["chain_valid"] is True
    assert data["total_records"] == 1
    assert data["details"][0]["valid"] is True


def test_audit_tampered_hash_detected(client, session):
    """Hash adulterado deve ser detectado na auditoria."""
    from datetime import date
    from database.models import Contract, EnergyGeneration, Organization, User, calculate_hash
    from app.core.security import create_hash_password

    org = Organization(name="TamperOrg", cnpj="77700000000177", email="tamper@org.com")
    session.add(org)
    session.flush()

    user = User(email="tamper@test.com", name="Tamper User", role="admin",
                organization_id=org.id, password_hash=create_hash_password("Password1@"))
    session.add(user)
    session.flush()

    c = Contract(number="TAMPER-001", organization_id=org.id, start_date=date(2026, 1, 1),
                 value_kwh=Decimal("0.85"), landlord_percentage=Decimal("0.30"), status="active")
    session.add(c)
    session.flush()

    g = EnergyGeneration(contract_id=c.id, organization_id=org.id,
                         reference_period=date(2026, 1, 1), energy_kwh=Decimal("1000"),
                         previous_hash=None, hash_sha256="")
    g.hash_sha256 = calculate_hash(g)
    session.add(g)
    session.flush()

    # Adulterar o hash diretamente no DB (simula ataque de integridade)
    g.hash_sha256 = "a" * 64
    session.add(g)
    session.commit()

    headers = auth_header(client, email="tamper@test.com")
    resp = client.post(f"/generation/{c.id}/audit", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["chain_valid"] is False
    assert data["invalid_records"] == 1
    assert data["details"][0]["valid"] is False
    assert "mismatch" in data["details"][0]["reason"].lower() or "altered" in data["details"][0]["reason"].lower()
