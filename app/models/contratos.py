from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.schemas import ContractCreate, ContractRead
from app.routers.auth import get_user
from database.database import get_session
from database.models import Contract, EnergyGeneration

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contract = Contract(**payload.model_dump(), organization_id=current_user.organization_id)
    session.add(contract)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contract number already exists.",
        ) from exc
    session.refresh(contract)
    return contract


@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: UUID,
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    if contract.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return contract


@router.put("/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: UUID,
    payload: ContractCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    if contract.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    has_generation = session.exec(
        select(EnergyGeneration).where(EnergyGeneration.contract_id == contract_id)
    ).first()

    current_percentage = contract.landlord_percentage or Decimal(0)
    if has_generation and payload.landlord_percentage != current_percentage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change landlord_percentage after generation records exist.",
        )

    for k, v in payload.model_dump().items():
        setattr(contract, k, v)
    contract.updated_at = datetime.now(timezone.utc)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contract number already exists.",
        ) from exc
    session.refresh(contract)
    return contract
