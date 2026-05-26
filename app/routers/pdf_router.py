from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session, select

from app.routers.auth import get_user
from app.services.pdf_service import DadosPDF, gerar_pdf
from database.database import get_session
from database.models import Contract, EnergyGeneration, Organization, User

router = APIRouter(prefix="/pdf", tags=["PDF"])

_SCEE_DISCOUNT = Decimal("0.95")


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

    landlord = session.exec(
        select(User).where(
            User.organization_id == current_user.organization_id,
            User.role == "locador",
        )
    ).first()
    landlord_name = landlord.name if landlord else current_user.name

    org = session.get(Organization, current_user.organization_id)
    tenant_name = org.name if org else current_user.name
    filename = f"solarize_{generation.reference_period.strftime('%Y-%m')}.pdf"

    try:
        dados = DadosPDF(
            locador=landlord_name,
            locatario=tenant_name,
            inicio_contrato=contract.start_date,
            energia_kwh=Decimal(str(generation.energy_kwh)),
            tarifa_kwh=Decimal(str(contract.value_kwh)),
            percentual_locador=Decimal(str(contract.landlord_percentage or 0)),
            desconto_scee=_SCEE_DISCOUNT,
            hash_sha256=generation.hash_sha256,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")

    return Response(
        content=gerar_pdf(dados),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


