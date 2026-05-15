from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from decimal import Decimal
from app.schemas.generation import *
from app.routers.auth import get_user
from app.services.hash_service import landlord_calculator
from database.database import get_session
from database.models import Contrato, User

router = APIRouter()


@router.post("/preview", response_model=Preview_Response)
def preview_dashboard(
    item: Preview_Request,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
):
    contract = session.exec(select(Contrato).where(Contrato.number == item.contract_ID)).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    tariff = Decimal(str(contract.value_kwh))
    percentage = Decimal(str(contract.percentual_locador or 0))
    value = landlord_calculator(item.generated_energy, tariff, percentage)

    return Preview_Response(
        generated_energy=str(item.generated_energy),
        tariff=str(tariff),
        landlord_percentage=str(percentage),
        loss_factor="0.95",
        formula=f"{item.generated_energy} × {tariff} × 0.95 × {percentage}",
        value=str(value),
        date=item.date.isoformat(),
        saved=False,
    )
