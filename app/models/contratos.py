from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.schemas import ContratoCreate, ContratoRead
from app.routers.auth import get_user
from database.database import get_session
from database.models import Contrato, GeracaoEnergia

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.post("/", response_model=ContratoRead, status_code=status.HTTP_201_CREATED)
def criar_contrato(
    payload: ContratoCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contrato = Contrato(**payload.model_dump(), organization_id=current_user.organization_id)
    session.add(contrato)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Número de contrato já existe.",
        ) from exc
    session.refresh(contrato)
    return contrato


@router.get("/", response_model=list[ContratoRead])
def listar_contratos(
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    return session.exec(
        select(Contrato).where(Contrato.organization_id == current_user.organization_id)
    ).all()


@router.get("/{contrato_id}", response_model=ContratoRead)
def obter_contrato(
    contrato_id: UUID,
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado.")
    if contrato.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    return contrato


@router.put("/{contrato_id}", response_model=ContratoRead)
def atualizar_contrato(
    contrato_id: UUID,
    payload: ContratoCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado.")
    if contrato.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    tem_geracao = session.exec(
        select(GeracaoEnergia).where(GeracaoEnergia.contrato_id == contrato_id)
    ).first()

    # Comparação segura: converte ambos para Decimal antes de comparar,
    # evitando divergência entre Decimal (payload) e float (banco de dados).
    percentual_atual = Decimal(str(contrato.percentual_locador or 0))
    percentual_novo = Decimal(str(payload.percentual_locador))
    if tem_geracao and percentual_novo != percentual_atual:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é permitido alterar percentual_locador após registros de geração.",
        )

    for k, v in payload.model_dump().items():
        setattr(contrato, k, v)
    contrato.updated_at = datetime.now(timezone.utc)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Número de contrato já existe.",
        ) from exc
    session.refresh(contrato)
    return contrato
