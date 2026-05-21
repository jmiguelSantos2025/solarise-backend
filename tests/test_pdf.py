"""Tests for GET /pdf/{geracao_id} — real DB data PDF download."""
from uuid import uuid4

from tests.conftest import auth_header, create_contract, register_user


def _setup_with_generation(client):
    """Register user, create contract, create generation. Returns (headers, geracao_id)."""
    register_user(client)
    headers = auth_header(client)
    create_contract(client, headers, number="CTRT-PDF", value_kwh="0.80",
                    percentual_locador="0.30")
    resp = client.post("/generation/", json={
        "contract_ID": "CTRT-PDF",
        "generated_energy": "1000.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers)
    assert resp.status_code == 201
    return headers, resp.json()["ID"]


def test_pdf_returns_real_data(client):
    headers, geracao_id = _setup_with_generation(client)

    resp = client.get(f"/pdf/{geracao_id}", headers=headers)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    assert "solarize_2026-03" in resp.headers["content-disposition"]
    assert resp.content[:4] == b"%PDF"


def test_pdf_requires_auth(client):
    resp = client.get(f"/pdf/{uuid4()}")
    assert resp.status_code == 401


def test_pdf_unknown_geracao_returns_404(client):
    register_user(client)
    headers = auth_header(client)
    resp = client.get(f"/pdf/{uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_pdf_rejects_invalid_uuid(client):
    register_user(client)
    headers = auth_header(client)
    resp = client.get("/pdf/not-a-uuid", headers=headers)
    assert resp.status_code == 422


def test_pdf_org_scoping(client):
    """Usuário de Org B não pode baixar PDF de geração de Org A."""
    # Org A cria geração
    register_user(client, email="a@test.com", name="User A",
                  org_name="OrgA", org_cnpj="11111111000101", org_email="a@org.com")
    headers_a = auth_header(client, email="a@test.com")
    create_contract(client, headers_a, number="CTRT-A", value_kwh="0.80",
                    percentual_locador="0.30")
    r = client.post("/generation/", json={
        "contract_ID": "CTRT-A", "generated_energy": "500.0",
        "date": "2026-03-01T00:00:00",
    }, headers=headers_a)
    geracao_id = r.json()["ID"]

    # Org B tenta acessar
    register_user(client, email="b@test.com", name="User B",
                  org_name="OrgB", org_cnpj="22222222000202", org_email="b@org.com")
    headers_b = auth_header(client, email="b@test.com")
    resp = client.get(f"/pdf/{geracao_id}", headers=headers_b)
    assert resp.status_code == 404
