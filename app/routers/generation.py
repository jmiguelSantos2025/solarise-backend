from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.routers.auth import get_user
from app.schemas.generation import (
    Generation_Request,
    Generation_Response,
    Preview_Request,
    Preview_Response,
)
from app.services.hash_service import landlord_calculator
from database.database import get_session
from database.models import Contrato, GeracaoEnergia, User, calcular_hash

router = APIRouter()


@router.post("/preview", response_model=Preview_Response)
def preview_generation(
    item: Preview_Request,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
):
    contract = session.exec(
        select(Contrato).where(
            Contrato.number == item.contract_ID,
            Contrato.organization_id == current_user.organization_id,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

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


@router.post("/", response_model=Generation_Response, status_code=status.HTTP_201_CREATED)
def create_generation(
    item: Generation_Request,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
):
    contract = session.exec(
        select(Contrato).where(
            Contrato.number == item.contract_ID,
            Contrato.organization_id == current_user.organization_id,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    last = session.exec(
        select(GeracaoEnergia)
        .where(GeracaoEnergia.contrato_id == contract.id)
        .order_by(GeracaoEnergia.created_at.desc())
    ).first()

    # Build the record first so calcular_hash can use the auto-generated id.
    geracao = GeracaoEnergia(
        contrato_id=contract.id,
        organization_id=current_user.organization_id,
        periodo_ref=item.date.date(),
        energia_kwh=float(item.generated_energy),
        hash_anterior=last.hash_sha256 if last else None,
        created_by=current_user.id,
    )
    geracao.hash_sha256 = calcular_hash(geracao)

    try:
        session.add(geracao)
        session.commit()
        session.refresh(geracao)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate generation record detected. Possible duplicate submission.",
        )

    tariff = Decimal(str(contract.value_kwh))
    percentage = Decimal(str(contract.percentual_locador or 0))
    value = landlord_calculator(item.generated_energy, tariff, percentage)

    return Generation_Response(
        ID=str(geracao.id),
        contract_ID=contract.number,
        value=value,
        hash_sha256=geracao.hash_sha256,
        previous_hash=geracao.hash_anterior,
        date=geracao.created_at,
    )
