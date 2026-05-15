from fastapi import APIRouter, Depends
from sqlmodel import Session,select
from decimal import Decimal, ROUND_HALF_UP
from database import get_session
from models import Contrato, GeracaoEnergia
from app.routers.auth import get_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/locador")
def dashboard_locador(
    session: Session = Depends(get_session),
    current_user = Depends(get_user),
):
    contrato = session.exec(
        select(Contrato).where(Contrato.org_id == current_user.org_id)
    ).first()
    if not contrato:
        return {"mes_atual": None, "serie_historica": []}
    geracoes = session.exec(
        select(GeracaoEnergia).where(GeracaoEnergia.contrato_id == contrato.id).order_by(GeracaoEnergia.periodo_ref)

    ).all()
    if not geracoes:
        return {"mes_atual": None, "serie_historica": []}
    def calc(g):
        v = (Decimal(str(g.energia_kwh))*contrato.tarifa_kwh*contrato.percentual_locador*Decimal("0.95"))
        return float(v.quantize(Decimal("0.01"),rounding = ROUND_HALF_UP))
    ultimas = geracoes[-1]
    return {
        "mes_atual": {"mes": ultimas.periodo_ref.strftime("%Y-%m"),"kwh": float(ultimas.energia_kwh), "valor":calc(ultimas), "hash":ultimas.hash_sha256},
        "serie_historica": [{"mes": g.periodo_ref.strftime("%Y-%m"), "valor": calc(g) } 
        for g in geracoes[-3:]]
    }