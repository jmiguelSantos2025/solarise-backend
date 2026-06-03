import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.routers.auth import get_user
from app.schemas.generation import Generation_Response, GenerationRequest, PreviewResponse
from database.database import get_session
from database.models import Contract, EnergyGeneration, User
from database.models import calculate_hash

router = APIRouter()

_SCEE = Decimal("0.95")
_QUANT = Decimal("0.01")


def _calc_value(energy_kwh: Decimal, value_kwh: Decimal, landlord_pct: Decimal) -> Decimal:
    return (energy_kwh * value_kwh * landlord_pct * _SCEE).quantize(_QUANT, rounding=ROUND_HALF_UP)


@router.post("/preview", response_model=PreviewResponse)
def preview(item: GenerationRequest, current_user: User = Depends(get_user), session: Session = Depends(get_session)):
    contract = session.exec(
        select(Contract).where(
            Contract.number == item.contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    energy = item.generated_energy
    value = _calc_value(energy, contract.value_kwh, contract.landlord_percentage or Decimal(0))

    return PreviewResponse(
        generated_energy=str(energy),
        tariff=str(contract.value_kwh),
        landlord_percentage=str(contract.landlord_percentage),
        loss_factor="0.95",
        formula=f"{energy} × {contract.value_kwh} × {contract.landlord_percentage} × 0.95",
        value=str(value),
        date=item.date.isoformat(),
        saved=False,
    )


@router.post("/", response_model=Generation_Response, status_code=status.HTTP_201_CREATED)
def create_generation(data: GenerationRequest, current_user: User = Depends(get_user), session: Session = Depends(get_session)):
    contract = session.exec(
        select(Contract).where(
            Contract.number == data.contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    ref_date = data.date.date() if hasattr(data.date, "date") else data.date
    duplicate = session.exec(
        select(EnergyGeneration).where(
            EnergyGeneration.contract_id == contract.id,
            EnergyGeneration.reference_period == ref_date,
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Generation for {ref_date} already registered.")

    last = session.exec(
        select(EnergyGeneration)
        .where(EnergyGeneration.contract_id == contract.id)
        .order_by(EnergyGeneration.created_at.desc())
    ).first()
    previous_hash = last.hash_sha256 if last else None

    gen_id = uuid.uuid4()
    value = _calc_value(data.generated_energy, contract.value_kwh, contract.landlord_percentage or Decimal(0))

    generation = EnergyGeneration(
        id=gen_id,
        contract_id=contract.id,
        organization_id=current_user.organization_id,
        reference_period=ref_date,
        energy_kwh=data.generated_energy,
        previous_hash=previous_hash,
        hash_sha256="",
        created_by=current_user.id,
    )
    generation.hash_sha256 = calculate_hash(generation)

    session.add(generation)
    session.commit()
    session.refresh(generation)

    return Generation_Response(
        ID=str(generation.id),
        contract_ID=contract.number,
        value=value,
        hash_sha256=generation.hash_sha256,
        previous_hash=generation.previous_hash,
        date=datetime.combine(generation.reference_period, datetime.min.time()).replace(tzinfo=timezone.utc),
    )


@router.post("/{contract_id}/audit")
def audit(contract_id: uuid.UUID, current_user: User = Depends(get_user), session: Session = Depends(get_session)):
    generations = session.exec(
        select(EnergyGeneration)
        .where(
            EnergyGeneration.contract_id == contract_id,
            EnergyGeneration.organization_id == current_user.organization_id,
        )
        .order_by(EnergyGeneration.created_at)
    ).all()
    if not generations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No records found for this contract.")

    result = []
    for i, g in enumerate(generations):
        expected_previous = generations[i - 1].hash_sha256 if i > 0 else None
        expected_hash = calculate_hash(g)
        valid = g.hash_sha256 == expected_hash and g.previous_hash == expected_previous
        result.append({
            "id": str(g.id),
            "valid": valid,
            "reason": "Valid hash" if valid else "Hash mismatch — record may have been altered.",
        })

    return {
        "contract_id": contract_id,
        "chain_valid": all(r["valid"] for r in result),
        "total_records": len(result),
        "valid_records": sum(1 for r in result if r["valid"]),
        "invalid_records": sum(1 for r in result if not r["valid"]),
        "details": result,
    }
