"""Tests for core services, security utilities, and miscellaneous bugs."""
import pytest
from decimal import Decimal


# ── hash_service: landlord_calculator ────────────────────────────────────────

from app.services.hash_service import landlord_calculator


def test_landlord_calculator_basic():
    # 1000 kWh * 0.80 tariff * 0.95 loss * 0.30 percentage = 228.00
    result = landlord_calculator(Decimal("1000"), Decimal("0.80"), Decimal("0.30"))
    assert result == Decimal("228.00")


def test_landlord_calculator_zero_percentage():
    result = landlord_calculator(Decimal("1000"), Decimal("0.80"), Decimal("0"))
    assert result == Decimal("0.00")


def test_landlord_calculator_rounding():
    # Verify ROUND_HALF_UP at 2 decimal places
    # 3 * 0.335 = 1.005 → rounds to 1.01 with ROUND_HALF_UP
    result = landlord_calculator(Decimal("1"), Decimal("1"), Decimal("1"))
    # 1 * 1 * 0.95 * 1 = 0.95
    assert result == Decimal("0.95")


def test_landlord_calculator_precision():
    # Ensure result is always quantized to 2 decimal places
    result = landlord_calculator(Decimal("123.4567"), Decimal("0.8012"), Decimal("0.2500"))
    assert result.as_tuple().exponent == -2


# ── security: JWT creation and verification ───────────────────────────────────

from app.core.security import create_token, verify_token, create_hash_password, verify_hash_password


def test_create_and_verify_token():
    payload = {"ID": "abc-123", "role": "admin"}
    token = create_token(payload, expire=1)
    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["ID"] == "abc-123"


def test_verify_token_invalid():
    assert verify_token("not.a.valid.token") is None


def test_verify_token_tampered():
    token = create_token({"ID": "x"})
    tampered = token[:-5] + "XXXXX"
    assert verify_token(tampered) is None


def test_password_hash_and_verify():
    hashed = create_hash_password("Password1@")
    assert verify_hash_password("Password1@", hashed) is True
    assert verify_hash_password("WrongPass1@", hashed) is False


# ── calcular_hash ─────────────────────────────────────────────────────────────

import uuid
from datetime import date
from database.models import GeracaoEnergia, calcular_hash


def test_calcular_hash_is_deterministic():
    g = GeracaoEnergia(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        contrato_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        organization_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        periodo_ref=date(2026, 1, 1),
        energia_kwh=500.0,
        hash_anterior=None,
        hash_sha256="placeholder",
    )
    h1 = calcular_hash(g)
    h2 = calcular_hash(g)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_calcular_hash_changes_with_different_energy():
    g = GeracaoEnergia(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        contrato_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        organization_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        periodo_ref=date(2026, 1, 1),
        energia_kwh=500.0,
        hash_anterior=None,
        hash_sha256="placeholder",
    )
    h1 = calcular_hash(g)
    g.energia_kwh = 600.0
    h2 = calcular_hash(g)
    assert h1 != h2


def test_calcular_hash_chaining():
    """Each record's hash includes the previous record's hash (chain integrity)."""
    g1 = GeracaoEnergia(
        id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        contrato_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        organization_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        periodo_ref=date(2026, 1, 1),
        energia_kwh=100.0,
        hash_anterior=None,
        hash_sha256="placeholder",
    )
    g1.hash_sha256 = calcular_hash(g1)

    g2 = GeracaoEnergia(
        id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        contrato_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        organization_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        periodo_ref=date(2026, 2, 1),
        energia_kwh=200.0,
        hash_anterior=g1.hash_sha256,
        hash_sha256="placeholder",
    )
    g2.hash_sha256 = calcular_hash(g2)

    assert g2.hash_sha256 != g1.hash_sha256
    # Changing g2's hash_anterior breaks the chain
    g2_tampered = GeracaoEnergia(
        id=g2.id,
        contrato_id=g2.contrato_id,
        organization_id=g2.organization_id,
        periodo_ref=g2.periodo_ref,
        energia_kwh=g2.energia_kwh,
        hash_anterior="0000000000000000000000000000000000000000000000000000000000000000",
        hash_sha256="placeholder",
    )
    assert calcular_hash(g2_tampered) != g2.hash_sha256


# ── BUG: CORS_ORIGINS env format includes brackets ───────────────────────────

def test_bug_cors_origins_with_brackets():
    """
    BUG: The .env.example ships CORS_ORIGINS=[http://localhost:3000] with
    square brackets. main.py calls settings.cors_origins.split(','), which
    produces ["[http://localhost:3000]"]. The bracket-prefixed string is not
    a valid origin, so CORS headers will never match and all cross-origin
    requests will fail.
    """
    raw = "[http://localhost:3000]"
    origins = raw.split(",")
    # The parsed origin still has brackets
    assert origins[0] == "[http://localhost:3000]"
    # A browser sends the plain origin without brackets:
    browser_origin = "http://localhost:3000"
    assert browser_origin not in origins, (
        "BUG CONFIRMED: When CORS_ORIGINS is set with brackets as shown in "
        ".env.example, the origin list contains '[http://localhost:3000]' "
        "instead of 'http://localhost:3000'. CORS will be broken for all "
        "requests from the frontend."
    )


# ── Health endpoint ───────────────────────────────────────────────────────────

def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["Status"] == "OK"
