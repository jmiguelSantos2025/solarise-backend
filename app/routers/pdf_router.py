from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session, select

from app.routers.auth import get_user
from app.services.pdf_service import DadosPDF, gerar_pdf
from database.database import get_session
from database.models import Contract, EnergyGeneration, User

router = APIRouter(prefix="/pdf", tags=["PDF"])

_SCEE_DISCOUNT = Decimal("0.95")

_MONTHS = {
    1: "January",   2: "February", 3: "March",    4: "April",
    5: "May",       6: "June",     7: "July",      8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


@router.get(
    "/{generation_id}",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Landlord generation report"},
        401: {"description": "Invalid or missing token"},
        404: {"description": "Generation record not found"},
    },
)
def download_pdf(
    generation_id: UUID,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
) -> Response:
    generation = session.exec(
        select(EnergyGeneration).where(
            EnergyGeneration.id == generation_id,
            EnergyGeneration.organization_id == current_user.organization_id,
        )
    ).first()
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation record not found or access denied.",
        )

    contract = session.get(Contract, generation.contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract associated with this generation record not found.",
        )

    landlord_name = _resolve_landlord(generation, current_user, session)
    reference_month = f"{_MONTHS[generation.reference_period.month]}/{generation.reference_period.year}"
    filename = f"solarize_{generation.reference_period.strftime('%Y-%m')}.pdf"

    dados = DadosPDF(
        locador=landlord_name,
        mes_ref=reference_month,
        energia_kwh=generation.energy_kwh,
        tarifa_kwh=contract.value_kwh,
        percentual_locador=contract.landlord_percentage or Decimal(0),
        desconto_scee=_SCEE_DISCOUNT,
        hash_sha256=generation.hash_sha256,
    )

    return Response(
        content=gerar_pdf(dados),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _resolve_landlord(generation: EnergyGeneration, current_user: User, session: Session) -> str:
    if generation.created_by:
        creator = session.get(User, generation.created_by)
        if creator:
            return creator.name
    return current_user.name
