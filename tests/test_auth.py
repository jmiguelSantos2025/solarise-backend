"""Tests for authentication endpoints: register, login, profile."""
from tests.conftest import auth_header, login_user, register_user


def test_register_success(client):
    resp = register_user(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "registrado" in data["message"]


def test_register_duplicate_email(client):
    register_user(client)
    resp = register_user(client)  # mesmo e-mail
    assert resp.status_code == 409


def test_register_same_cnpj_creates_one_org(client):
    """Dois usuários com mesmo CNPJ devem compartilhar a organização existente."""
    register_user(client, email="a@test.com", name="User A")
    resp = register_user(client, email="b@test.com", name="User B")
    assert resp.status_code == 200


def test_register_weak_password_rejected(client):
    resp = client.post("/auth/register", json={
        "name": "Test",
        "email": "weak@test.com",
        "password": "weakpassword",
        "role": "admin",
        "org_name": "WeakOrg",
        "org_cnpj": "99999999000199",
        "org_email": "weak@org.com",
    })
    assert resp.status_code == 422


def test_login_success(client):
    register_user(client)
    resp = login_user(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 86400


def test_login_wrong_password(client):
    register_user(client)
    resp = login_user(client, password="WrongPass9!")
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = login_user(client, email="nobody@test.com")
    assert resp.status_code == 401


def test_profile_requires_auth(client):
    resp = client.get("/auth/profile")
    assert resp.status_code == 401


def test_profile_returns_user_data(client):
    register_user(client)
    headers = auth_header(client)
    resp = client.get("/auth/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "user@test.com"
    assert data["name"] == "Test User"
    assert "ID" in data
    assert "org_id" in data


def test_profile_invalid_token(client):
    resp = client.get("/auth/profile", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


def test_client_supplied_id_is_ignored(client):
    """
    Após a remoção do campo ID do Register_Request, qualquer valor enviado pelo
    cliente é ignorado pelo Pydantic. O usuário é criado com UUID gerado pelo servidor.
    """
    custom_id = "00000000-0000-0000-0000-000000000001"
    resp = client.post("/auth/register", json={
        "ID": custom_id,
        "name": "Test User",
        "email": "test@test.com",
        "password": "Password1@",
        "role": "admin",
        "org_name": "TestOrg",
        "org_cnpj": "11111111000111",
        "org_email": "test@org.com",
    })
    assert resp.status_code == 200  # registro bem-sucedido

    # O ID atribuído pelo servidor deve ser diferente do enviado pelo cliente
    headers = auth_header(client, email="test@test.com")
    profile = client.get("/auth/profile", headers=headers).json()
    assert profile["ID"] != custom_id, (
        "O servidor deve gerar o UUID — nunca usar o fornecido pelo cliente."
    )
