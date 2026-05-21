from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from app.routers.auth import get_user
from database.database import get_session
from database.models import Contrato, GeracaoEnergia

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_ZERO = Decimal("0")
_QUANT_KWH = Decimal("0.0001")
_QUANT_BRL = Decimal("0.01")


def _calc_valor(g: GeracaoEnergia, contrato: Contrato) -> Decimal:
    return (
        Decimal(str(g.energia_kwh))
        * Decimal(str(contrato.value_kwh))
        * Decimal(str(contrato.percentual_locador or 0))
        * Decimal("0.95")
    ).quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)


@router.get("/locador")
def dashboard_locador(
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    contratos = session.exec(
        select(Contrato).where(Contrato.organization_id == current_user.organization_id)
    ).all()
    if not contratos:
        return {"mes_atual": None, "serie_historica": []}

    contrato_map = {c.id: c for c in contratos}

    geracoes = session.exec(
        select(GeracaoEnergia)
        .where(col(GeracaoEnergia.contrato_id).in_(list(contrato_map.keys())))
        .order_by(GeracaoEnergia.periodo_ref, GeracaoEnergia.created_at)
    ).all()
    if not geracoes:
        return {"mes_atual": None, "serie_historica": []}

    # Agrega kWh, valor financeiro e hash (último da chain) por mês.
    monthly: dict[str, dict] = defaultdict(lambda: {"kwh": _ZERO, "valor": _ZERO, "hash": None})
    for g in geracoes:
        mes = g.periodo_ref.strftime("%Y-%m")
        monthly[mes]["kwh"] += Decimal(str(g.energia_kwh))
        monthly[mes]["valor"] += _calc_valor(g, contrato_map[g.contrato_id])
        monthly[mes]["hash"] = g.hash_sha256  # ponta da chain neste mês

    sorted_months = sorted(monthly.keys())
    last_mes = sorted_months[-1]

    return {
        "mes_atual": {
            "mes": last_mes,
            "kwh": float(monthly[last_mes]["kwh"].quantize(_QUANT_KWH, rounding=ROUND_HALF_UP)),
            "valor": float(monthly[last_mes]["valor"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
            "hash": monthly[last_mes]["hash"],
        },
        "serie_historica": [
            {
                "mes": mes,
                "valor": float(monthly[mes]["valor"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
            }
            for mes in sorted_months[-3:]
        ],
    }
