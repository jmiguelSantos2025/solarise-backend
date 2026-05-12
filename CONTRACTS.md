# Solarize API Contracts

**Base URL (dev):** `http://localhost:8000`
**Base URL (prod):** `https://solarize-api.railway.app`

> 🔒 = requires `Authorization: Bearer {access_token}`

---

## POST /auth/register

**Authentication:** None

**Request Body:**
```json
{
  "name": "SolarTech",
  "email": "contact@solartech.com",
  "password": "Password123@$",
  "role": "Administrator"
}
```

| Field    | Type   | Rules                                                   |
|----------|--------|---------------------------------------------------------|
| name     | string | 2–100 characters                                        |
| email    | string | Valid email format                                      |
| password | string | Min 8 chars, upper, lower, number and special character |
| role     | string | `"Administrator"` or `"Analyst"`                        |

**Responses:**

`201`
```json
{
  "message": "Installer registered successfully.",
  "success": true
}
```

`409`
```json
{ "detail": "Email already registered." }
```

`422`
```json
{ "detail": "Invalid password format." }
```

---

## POST /auth/login

**Authentication:** None — rate limit: 10 attempts per IP every 15 minutes

**Request Body:**
```json
{
  "email": "contact@solartech.com",
  "password": "Password123@$"
}
```

**Responses:**

`200`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "NYvt238B92j2HF27jG12H1kd03...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

`401`
```json
{ "detail": "Invalid credentials." }
```

`429`
```json
{ "detail": "Too many attempts. Try again in 15 minutes." }
```

---

## POST /auth/refresh

**Authentication:** None — uses `refresh_token` in body

**Request Body:**
```json
{
  "refresh_token": "NYvt238B92j2HF27jG12H1kd03..."
}
```

**Responses:**

`200`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "NYvt238B92j2HF27jG12H1kd03...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

`401`
```json
{ "detail": "Invalid or expired refresh token." }
```

---

## POST /auth/invite

🔒 **Authentication:** Required — `role: Administrator` only

**Request Body:**
```json
{
  "name": "John",
  "email": "john@gmail.com"
}
```

**Responses:**

`200`
```json
{
  "message": "Invite sent to john@gmail.com.",
  "success": true
}
```

`403`
```json
{ "detail": "Only administrators can invite users." }
```

`401`
```json
{ "detail": "Invalid or expired token." }
```

---

## GET /auth/me

🔒 **Authentication:** Required

**Request Body:** None

**Responses:**

`200`
```json
{
  "ID": 1,
  "name": "SolarTech",
  "email": "contact@solartech.com",
  "org_id": "f1e2d3c4-b5a6-7890-abcd-123456789abc",
  "role": "Administrator"
}
```

`401`
```json
{ "detail": "Invalid or expired token." }
```

`404`
```json
{ "detail": "User not found." }
```

---

## POST /geracao/preview

🔒 **Authentication:** Required

**Request Body:**
```json
{
  "contract_ID": "ctrt-001",
  "generated_energy": 38500.00,
  "date": "2026-03-01T00:00:00"
}
```

**Responses:**

`200`
```json
{
  "generated_energy": 38500.00,
  "value": 9325.50,
  "date": "2026-03-01T00:00:00"
}
```

`404`
```json
{ "detail": "Contract not found." }
```

---

## POST /geracao/

🔒 **Authentication:** Required

**Request Body:**
```json
{
  "contract_ID": "ctrt-001",
  "generated_energy": 38500.00,
  "date": "2026-03-01T00:00:00"
}
```

**Responses:**

`201`
```json
{
  "ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

`409`
```json
{ "detail": "Generation for this period already registered." }
```

`404`
```json
{ "detail": "Contract not found." }
```

---

## POST /geracao/csv

🔒 **Authentication:** Required

**Request:** `multipart/form-data`

| Field       | Type        | Description        |
|-------------|-------------|--------------------|
| contract_ID | query param | Target contract ID |
| file        | file        | `.csv` file        |

**Required CSV columns:** `date`, `generated_energy`

```
date,generated_energy
2026-01-01T00:00:00,38500.00
2026-02-01T00:00:00,41200.00
```

**Responses:**

`200`
```json
{
  "total_rows": 2,
  "valid_rows": 2,
  "invalid_rows": 0,
  "preview": [
    { "date": "2026-01-01T00:00:00", "generated_energy": "38500.00", "valid": true, "error": null },
    { "date": "2026-02-01T00:00:00", "generated_energy": "41200.00", "valid": true, "error": null }
  ],
  "message": "Valid CSV. Confirm to import."
}
```

`400`
```json
{ "detail": "File must be a .csv." }
```

`422`
```json
{ "detail": "Missing columns: {'generated_energy'}. Found: ['date']" }
```

---

## GET /geracao/{contract_ID}/audit

🔒 **Authentication:** Required

**Path Parameter:** `contract_ID`

**Request Body:** None

**Responses:**

`200` — chain intact
```json
{
  "contract_ID": "ctrt-001",
  "chain_valid": true,
  "total_records": 3,
  "valid_records": 3,
  "invalid_records": 0,
  "details": [
    { "ID": "a1b2...", "date": "2026-01-01T00:00:00", "valid": true, "reason": "OK" },
    { "ID": "b2c3...", "date": "2026-02-01T00:00:00", "valid": true, "reason": "OK" },
    { "ID": "c3d4...", "date": "2026-03-01T00:00:00", "valid": true, "reason": "OK" }
  ]
}
```

`200` — tampering detected
```json
{
  "contract_ID": "ctrt-001",
  "chain_valid": false,
  "total_records": 3,
  "valid_records": 1,
  "invalid_records": 2,
  "details": [
    { "ID": "a1b2...", "date": "2026-01-01T00:00:00", "valid": true,  "reason": "OK" },
    { "ID": "b2c3...", "date": "2026-02-01T00:00:00", "valid": false, "reason": "Hash mismatch — record was altered." },
    { "ID": "c3d4...", "date": "2026-03-01T00:00:00", "valid": false, "reason": "Previous hash mismatch." }
  ]
}
```

`404`
```json
{ "detail": "No records found for this contract." }
```

---

## GET /health

**Authentication:** None

**Responses:**

`200`
```json
{ "status": "ok", "version": "1.0.0" }
```
