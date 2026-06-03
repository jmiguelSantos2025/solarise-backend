"""
Testes de integração — Semana 5 | Solarize
Verifica o fluxo completo end-to-end sem depender do banco remoto.
"""
import uuid
from decimal import Decimal

from tests.conftest import auth_header, create_contract, register_user


def test_fluxo_completo(client):
    """
    Fluxo completo da demo: registrar -> login -> contrato -> 3 gerações -> dashboard -> PDF.
    Replica os dados do seed (CONT-001, 38500 kWh mar/26 = R$ 9.325,50).
    """
    # 1. Registrar usuário instaladora e logar
    register_user(
        client,
        email="instaladora@solartech.am",
        password="Solarize2026@",
        name="Admin SolarTech",
        role="instaladora",
        org_name="SolarTech AM",
        org_cnpj="12345678000199",
        org_email="contato@solartech.am",
    )
    headers = auth_header(client, email="instaladora@solartech.am", password="Solarize2026@")

    # 2. Criar contrato (tarifas idênticas ao seed)
    resp = create_contract(
        client, headers,
        number="CONT-001",
        value_kwh="0.85",
        percentual_locador="0.30",
        start_date="2026-01-01",
    )
    assert resp.status_code == 201, f"Criação de contrato falhou: {resp.text}"
    contratos = client.get("/contracts/", headers=headers).json()
    assert len(contratos) > 0, "Nenhum contrato encontrado — seed não foi aplicado?"
    print(f"  Contratos encontrados: {len(contratos)}")

    # 3. Registrar 3 meses de geração (jan, fev, mar/26)
    meses = [
        ("2026-01-01T00:00:00", "36200"),
        ("2026-02-01T00:00:00", "34850"),
        ("2026-03-01T00:00:00", "38500"),
    ]
    last_gen_id = None
    for date_str, energy in meses:
        r = client.post("/generation/", json={
            "contract_id": "CONT-001",
            "generated_energy": energy,
            "date": date_str,
        }, headers=headers)
        assert r.status_code == 201, f"Geração {date_str} falhou: {r.text}"
        assert len(r.json()["hash_sha256"]) == 64, "Hash SHA-256 inválido"
        last_gen_id = r.json()["ID"]
    print(f"  3 gerações registradas — último ID: {last_gen_id[:8]}...")

    # 4. Dashboard deve refletir mar/26 como mês atual com R$ 9.325,50
    resp = client.get("/dashboard/landlord", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_month"] is not None, "Dashboard vazio — geração não foi salva?"
    assert data["current_month"]["month"] == "2026-03"
    # 38500 × 0.85 × 0.30 × 0.95 = 9326.625 → ROUND_HALF_UP → 9326.63
    assert Decimal(str(data["current_month"]["value"])) == Decimal("9326.63"), (
        f"Valor errado: {data['current_month']['value']} (esperado 9326.63)"
    )
    assert len(data["historical_series"]) == 3, "Deve ter 3 meses no histórico"
    print(f"  Dashboard OK — valor: R$ {data['current_month']['value']}")

    # 5. PDF deve ser gerado com sucesso para o último registro
    resp = client.get(f"/pdf/{last_gen_id}", headers=headers)
    assert resp.status_code == 200, f"PDF falhou: {resp.status_code}"
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF", "Resposta não é um PDF válido"
    print(f"  PDF OK — {len(resp.content)} bytes")

    print("  Fluxo completo OK!")


def test_isolamento_org(client):
    """Verifica que endpoints retornam apenas dados da própria org."""
    # Org A cria contrato e geração
    register_user(client, email="a@solarize.com", name="User A",
                  org_name="OrgA", org_cnpj="11111111000101", org_email="a@org.com")
    headers_a = auth_header(client, email="a@solarize.com")
    create_contract(client, headers_a, number="CTRT-ORG-A")
    r = client.post("/generation/", json={
        "contract_id": "CTRT-ORG-A",
        "generated_energy": "1000",
        "date": "2026-03-01T00:00:00",
    }, headers=headers_a)
    gen_id_a = r.json()["ID"]
    contrato_id_a = client.get("/contracts/", headers=headers_a).json()[0]["id"]

    # Org B tenta acessar contrato e PDF da Org A
    register_user(client, email="b@solarize.com", name="User B",
                  org_name="OrgB", org_cnpj="22222222000202", org_email="b@org.com")
    headers_b = auth_header(client, email="b@solarize.com")

    resp_contrato = client.get(f"/contracts/{contrato_id_a}", headers=headers_b)
    assert resp_contrato.status_code in [403, 404], (
        f"Isolamento falhou para /contracts/: esperado 403 ou 404, recebeu {resp_contrato.status_code}"
    )

    resp_pdf = client.get(f"/pdf/{gen_id_a}", headers=headers_b)
    assert resp_pdf.status_code in [403, 404], (
        f"Isolamento falhou para /pdf/: esperado 403 ou 404, recebeu {resp_pdf.status_code}"
    )
    print("  Isolamento org OK!")


def test_endpoint_saude(client):
    """Verifica que o health check responde."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["Status"] == "OK"
    print("  Health check OK!")
