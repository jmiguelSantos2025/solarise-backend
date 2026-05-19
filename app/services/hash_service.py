from decimal import Decimal, ROUND_HALF_UP
from json import dumps
from hashlib import sha256

def landlord_calculator(energy: Decimal, tariff: float, percentage: float) -> Decimal: #Done!
    loss_factor = Decimal("0.95")
    value = loss_factor*energy*Decimal(tariff)*Decimal(percentage)
    return value.quantize(Decimal(value), rounding=ROUND_HALF_UP)

def hash_chain(data: dict, previous_hash: str) -> str: #Done!
    new_hash = dumps(data, sort_keys=True, default=str) + previous_hash
    return sha256(new_hash.encode("utf-8")).hexdigest()

def verify_hash_chain(registers: list) -> list: #Done!
    result = []
    for i, register in enumerate(registers):
        expected_previous_hash = "GENESIS" if i == 0 else registers[i-1]["hash_sha256"]
        if register["previous_hash"] != expected_previous_hash:
            result.append({
                "id": register["id"],
                "valid": False,
                "reason": "Previous hash mismatch — possible tampering in chain."
            })
            continue
        else:
            this_hash = hash_chain(register["data"], expected_previous_hash)
            if this_hash == register["hash_sha256"]:
                result.append({
                    "id": register["id"], 
                    "valid": True, 
                    "reason": "Valid hash"
                })
            else:
                result.append({
                    "id": register["id"],
                    "valid": False,
                    "reason": "Hash mismatch — record was altered after creation."
                })
    return result
