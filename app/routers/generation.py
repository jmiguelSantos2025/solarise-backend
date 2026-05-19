from fastapi import APIRouter, Depends, HTTPException
from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from app.schemas.generation import *
from app.routers.auth import get_user
from app.services.hash_service import landlord_calculator, hash_chain, verify_hash_chain

contracts = {"ctrt-001": {"tariff": 0.85, "landlord_percentage": 0.30}}

registers = []

router = APIRouter()

def get_previous_hash(contract_id: str, org_id: str) -> str:
    contract_registers = []
    for register in registers:
        if register["contract_id"] == contract_id and register["org_id"] == org_id:
            contract_registers.append(register)
        else:
            return "GENESIS"
    previous_register = sorted(contract_registers, key=lambda x: x["created_in"])[-1]
    return previous_register["hash_sha256"]

@router.post("/preview", response_model=Preview_Response)
def preview_dashboard(item: Preview_Request, current_user: dict = Depends(get_user)):
    contract = contracts.get(item.contract_ID)
    if not contract:
        raise HTTPException(status_code=404, detail="Error: Contract not found.")
    try:
        generated_energy = item.generated_energy
        tariff = contract["tariff"]
        percentage = contract["landlord_percentage"]
        value = landlord_calculator(generated_energy, tariff, percentage)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")
    return Preview_Response(
        generated_energy=str(generated_energy),
        tariff=str(tariff),
        landlord_percentage=str(percentage),
        loss_factor="0.95",
        formula=f"{generated_energy} × {tariff} × 0.95 × {percentage}",
        value=str(value),
        date=item.date.isoformat(),
        saved=False
    )

@router.post("/", response_model=Generation_Response, status_code=201)
def generation(data: Generation_Request, current_user: dict = Depends(get_user)):
    contract = contracts.get(data.contract_ID)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    
    if any(
            r["contract_id"] == data.contract_ID
            and r["org_id"] == current_user["org_id"]
            and r["date"].year == data.date.year
            and r["date"].month == data.date.month
            for r in registers):
        raise HTTPException(status_code=409, detail=f"Generation for {data.date.month} already registered.")
    
    generated_energy = data.generated_energy
    tariff = contract["tariff"]
    percentage = contract["percentage"]
    value = landlord_calculator(generated_energy, tariff, percentage)

    data_hash = {
        "contract_id": data.contract_ID,
        "date": data.date,
        "generated_energy": str(generated_energy),
        "tariff": str(tariff),
        "landlord_percentage": str(percentage),
        "value": str(value)
    }

    previous_hash = get_previous_hash(data.contract_ID, current_user["org_id"])
    new_hash = hash_chain(data_hash, previous_hash)
    register_id = str(uuid4())
    time_now = datetime.utcnow().isoformat()

    registers.append({
        "id": register_id,
        "contract_id": data.contract_ID,
        "org_id": current_user["org_id"],
        "date": data.date,
        "dados_para_hash": data_hash,
        "hash_sha256": new_hash,
        "previous_hash": previous_hash,
        "created_at": time_now
        })
    
    return Generation_Response(
        ID=register_id,
        contract_ID=data.contract_ID,
        value=str(value),
        hash_sha256=new_hash,
        previous_hash=previous_hash,
        date=datetime.fromisoformat(time_now)
    )


