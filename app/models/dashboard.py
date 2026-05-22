from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from app.routers.auth import get_user
from database.database import get_session
from database.models import Contract, EnergyGeneration

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_ZERO = Decimal("0")
_QUANT_KWH = Decimal("0.0001")
_QUANT_BRL = Decimal("0.01")


def _calc_value(g: EnergyGeneration, contract: Contract) -> Decimal:
    return (
        g.energy_kwh
        * contract.value_kwh
        * (contract.landlord_percentage or _ZERO)
        * Decimal("0.95")
    ).quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)


@router.get("/landlord")
def landlord_dashboard(
    session: Session = Depends(get_session),
    current_user=Depends(get_user),
):
    try:
        contracts = session.exec(
            select(Contract).where(Contract.organization_id == current_user.organization_id)
        ).all()
        if not contracts:
            return {"current_month": None, "historical_series": []}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    contract_map = {c.id: c for c in contracts}

    generations = session.exec(
        select(EnergyGeneration)
        .where(col(EnergyGeneration.contract_id).in_(list(contract_map.keys())))
        .order_by(col(EnergyGeneration.reference_period))
    ).all()
    if not generations:
        return {"current_month": None, "historical_series": []}

<<<<<<< HEAD
    monthly: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"kwh": _ZERO, "value": _ZERO})
    for g in generations:
        month = g.reference_period.strftime("%Y-%m")
        monthly[month]["kwh"] += g.energy_kwh
        monthly[month]["value"] += _calc_value(g, contract_map[g.contract_id])
=======
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
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7

    sorted_months = sorted(monthly.keys())
    last_month = sorted_months[-1]

    return {
<<<<<<< HEAD
        "current_month": {
            "month": last_month,
            "kwh": float(monthly[last_month]["kwh"].quantize(_QUANT_KWH, rounding=ROUND_HALF_UP)),
            "value": float(monthly[last_month]["value"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
=======
        "mes_atual": {
            "mes": last_mes,
            "kwh": float(monthly[last_mes]["kwh"].quantize(_QUANT_KWH, rounding=ROUND_HALF_UP)),
            "valor": float(monthly[last_mes]["valor"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
            "hash": monthly[last_mes]["hash"],
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7
        },
        "historical_series": [
            {
                "month": month,
                "value": float(monthly[month]["value"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
            }
            for month in sorted_months[-3:]
        ],
    }
