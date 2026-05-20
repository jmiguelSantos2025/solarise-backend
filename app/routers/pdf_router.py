from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.routers.auth import get_user
from app.services.pdf_service import DadosPDF, gerar_pdf
from database.models import User

router = APIRouter(prefix="/pdf", tags=["PDF"])

# Fixed data for S3 stub. Replace with DB query in S4.
_STUB: DadosPDF = DadosPDF(
    locador="Joao Silva",
    mes_ref="marco/2026",
    energia_kwh=Decimal("38500"),
    tarifa_kwh=Decimal("0.85"),
    percentual_locador=Decimal("0.30"),
    desconto_scee=Decimal("0.95"),
    hash_sha256="a3f8c2e1d4b7f9a0e2c5d8b1f4a7c0e3d6b9f2a5c8e1d4b7f0a3c6e9d2b5f8a1",
)


@router.get(
    "/{geracao_id}",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Relatório PDF do locador"},
        401: {"description": "Token inválido ou ausente"},
    },
)
def baixar_pdf(
    geracao_id: UUID,
    current_user: User = Depends(get_user),
) -> Response:
    # TODO S4: buscar dados reais do banco usando geracao_id
    pdf_bytes = gerar_pdf(_STUB)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="solarize_2026-03.pdf"'},
    )
