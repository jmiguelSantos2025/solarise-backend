from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session, select

from app.core.config import settings
from app.routers.auth import get_user
from app.services.pdf_service import DadosPDF, gerar_pdf
from database.database import get_session
<<<<<<< HEAD
from database.models import Contract, EnergyGeneration, User
=======
from database.models import Contrato, GeracaoEnergia, Organization, User
>>>>>>> d8633da (PDF - Design Concluido)

router = APIRouter(prefix="/pdf", tags=["PDF"])

_SCEE_DISCOUNT = Decimal("0.95")

<<<<<<< HEAD
_MONTHS = {
    1: "January",   2: "February", 3: "March",    4: "April",
    5: "May",       6: "June",     7: "July",      8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

=======
>>>>>>> d8633da (PDF - Design Concluido)

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
<<<<<<< HEAD
    generation = session.exec(
        select(EnergyGeneration).where(
            EnergyGeneration.id == generation_id,
            EnergyGeneration.organization_id == current_user.organization_id,
        )
    ).first()
    if not generation:
=======
    if settings.app_env == "development":
        geracao = session.get(GeracaoEnergia, geracao_id)
    else:
        geracao = session.exec(
            select(GeracaoEnergia).where(
                GeracaoEnergia.id == geracao_id,
                GeracaoEnergia.organization_id == current_user.organization_id,
            )
        ).first()
    if not geracao:
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7
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

<<<<<<< HEAD
<<<<<<< HEAD
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

=======
    locador_name = _resolve_locador(geracao, current_user, session)
    mes_ref = f"{_MESES[geracao.periodo_ref.month]}/{geracao.periodo_ref.year}"
=======
    org = session.get(Organization, current_user.organization_id)
    locador_name  = org.name if org else current_user.name
    locatario_name = _resolve_locador(geracao, current_user, session)
>>>>>>> d8633da (PDF - Design Concluido)
    filename = f"solarize_{geracao.periodo_ref.strftime('%Y-%m')}.pdf"
    try:
        dados = DadosPDF(
            locador=locador_name,
            locatario=locatario_name,
            inicio_contrato=contrato.start_date,
            energia_kwh=Decimal(str(geracao.energia_kwh)),
            tarifa_kwh=Decimal(str(contrato.value_kwh)),
            percentual_locador=Decimal(str(contrato.percentual_locador or 0)),
            desconto_scee=_DESCONTO_SCEE,
            hash_sha256=geracao.hash_sha256,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7
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
