import requests

BASE = "http://localhost:8000"

response = requests.post(f"{BASE}/auth/login", data={
    "username": "john.doe@contact.com", "password": "Password0@$"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

gen_response = requests.post(f"{BASE}/generation/", json={
    "contract_ID": "ctrt-001",
    "generated_energy": 38500,
    "date": "2026-03-01T00:00:00"
}, headers=headers)

print("New generation:", gen_response.status_code)

before = requests.post(f"{BASE}/generation/ctrt-001/audit", headers=headers).json()
print("Before:", before["chain_valid"])

requests.post(f"{BASE}/generation/ctrt-001/tamper-test", headers=headers)

after = requests.post(f"{BASE}/generation/ctrt-001/audit", headers=headers).json()
print("After:", after["chain_valid"]) 