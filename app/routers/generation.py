from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.routers.auth import get_user
from app.schemas.generation import (
    GenerationRequest,
    GenerationResponse,
    PreviewRequest,
    PreviewResponse,
)
from app.services.hash_service import landlord_calculator
from database.database import get_session
from database.models import Contract, EnergyGeneration, User, calculate_hash
from sqlmodel import col

router = APIRouter()


@router.post("/preview", response_model=PreviewResponse)
def preview_generation(
    item: PreviewRequest,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
):
    contract = session.exec(
        select(Contract).where(
            Contract.number == item.contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    tariff = contract.value_kwh
    percentage = contract.landlord_percentage or Decimal(0)
    value = landlord_calculator(item.generated_energy, tariff, percentage)

    return PreviewResponse(
        generated_energy=str(item.generated_energy),
        tariff=str(tariff),
        landlord_percentage=str(percentage),
        loss_factor="0.95",
        formula=f"{item.generated_energy} × {tariff} × 0.95 × {percentage}",
        value=str(value),
        date=item.date.isoformat(),
        saved=False,
    )


@router.post("/", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
def create_generation(
    item: GenerationRequest,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
):
    contract = session.exec(
        select(Contract).where(
            Contract.number == item.contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    last = session.exec(
        select(EnergyGeneration)
        .where(EnergyGeneration.contract_id == contract.id)
        .order_by(col(EnergyGeneration.created_at).desc())
    ).first()

    generation = EnergyGeneration(
        contract_id=contract.id,
        organization_id=current_user.organization_id,
        reference_period=item.date.date(),
        energy_kwh=item.generated_energy,
        hash_sha256="",
        previous_hash=last.hash_sha256 if last else None,
        created_by=current_user.id,
    )
    generation.hash_sha256 = calculate_hash(generation)

    try:
        session.add(generation)
        session.commit()
        session.refresh(generation)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate generation record detected. Possible duplicate submission.",
        )

    tariff = contract.value_kwh
    percentage = contract.landlord_percentage or Decimal(0)
    value = landlord_calculator(item.generated_energy, tariff, percentage)

    return GenerationResponse(
        id=str(generation.id),
        contract_id=contract.number,
        value=value,
        hash_sha256=generation.hash_sha256,
        previous_hash=generation.previous_hash,
        date=generation.created_at,
    )
