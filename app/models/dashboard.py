from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
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

    monthly: dict[str, dict] = defaultdict(lambda: {"kwh": _ZERO, "value": _ZERO, "hash": ""})
    for g in generations:
        month = g.reference_period.strftime("%Y-%m")
        monthly[month]["kwh"] += g.energy_kwh
        monthly[month]["value"] += _calc_value(g, contract_map[g.contract_id])
        monthly[month]["hash"] = g.hash_sha256  # last record in period order wins

    sorted_months = sorted(monthly.keys())
    last_month = sorted_months[-1]

    return {
        "current_month": {
            "month": last_month,
            "kwh": float(monthly[last_month]["kwh"].quantize(_QUANT_KWH, rounding=ROUND_HALF_UP)),
            "value": float(monthly[last_month]["value"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
            "hash": monthly[last_month]["hash"],
        },
        "historical_series": [
            {
                "month": month,
                "value": float(monthly[month]["value"].quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)),
            }
            for month in sorted_months[-3:]
        ],
    }
