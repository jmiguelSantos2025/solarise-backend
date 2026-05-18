from fastapi import APIRouter, Depends, HTTPException
from app.schemas.generation import *
from app.routers.auth import get_user
from app.services.hash_service import landlord_calculator

contracts = {"ctrt-001":{"tariff": 1.0, "landlord_percentage": 30.0}}

router = APIRouter()

@router.post("/preview", response_model=Preview_Response)
def preview_dashboard(item: Preview_Request, current_user: dict = Depends(get_user)):
    contract = contracts.get(item.contract_ID)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    try:
        generated_energy = item.generated_energy
        tariff = contract["tariff"]
        percentage = contract["landlord_percentage"]
        value = landlord_calculator(generated_energy, tariff, percentage)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{e}")
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