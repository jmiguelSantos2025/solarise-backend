"""Tests for GET /pdf/{geracao_id} — stub PDF download endpoint."""
from uuid import uuid4

from tests.conftest import auth_header, register_user

_ANY_UUID = str(uuid4())


def test_pdf_stub_returns_pdf(client):
    register_user(client)
    headers = auth_header(client)

    resp = client.get(f"/pdf/{_ANY_UUID}", headers=headers)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    assert "solarize" in resp.headers["content-disposition"]
    # PDF magic bytes
    assert resp.content[:4] == b"%PDF"


def test_pdf_requires_auth(client):
    resp = client.get(f"/pdf/{_ANY_UUID}")
    assert resp.status_code == 401


def test_pdf_rejects_invalid_uuid(client):
    register_user(client)
    headers = auth_header(client)
    resp = client.get("/pdf/not-a-uuid", headers=headers)
    assert resp.status_code == 422
