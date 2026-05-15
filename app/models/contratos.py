from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from uuid import UUID
from database.database import get_session
from database.models import Contrato, GeracaoEnergia
from app.models.schemas import ContratoCreate, ContratoRead
from app.routers.auth import get_user

router = APIRouter(prefix="/contratos", tags=["contratos"])

@router.post("/", response_model=ContratoRead,status_code=201)
def criar_contrato(
    payload: ContratoCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_user)
):
    contrato = Contrato(**payload.model_dump(), organization_id=current_user.organization_id)
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato

@router.get("/{contrato_id}", response_model=ContratoRead)
def obter_contrato(
    contrato_id: UUID,
    session: Session = Depends(get_session),
    current_user = Depends(get_user),

):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato nao encontrado")
    if contrato.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return contrato

@router.put("/{contrato_id}", response_model=ContratoRead)
def atualizar_contrato(
    contrato_id: UUID,
    payload: ContratoCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_user),
):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato nao encontrado")
    if contrato.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    tem_geracao = session.exec(
        select(GeracaoEnergia).where(GeracaoEnergia.contrato_id == contrato_id)).first()
    if tem_geracao and payload.percentual_locador != contrato.percentual_locador:
        raise HTTPException(status_code=409, detail="Nao alterar percentual_locador apos registros de geracao")
    for k, v in payload.model_dump().items():
        setattr(contrato,k,v)
    session.commit()
    session.refresh(contrato)
    return contrato