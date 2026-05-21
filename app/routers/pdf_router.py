from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session, select

from app.core.config import settings
from app.routers.auth import get_user
from app.services.pdf_service import DadosPDF, gerar_pdf
from database.database import get_session
from database.models import Contrato, GeracaoEnergia, User

router = APIRouter(prefix="/pdf", tags=["PDF"])

_DESCONTO_SCEE = Decimal("0.95")

_MESES = {
    1: "janeiro",  2: "fevereiro", 3: "março",    4: "abril",
    5: "maio",     6: "junho",     7: "julho",     8: "agosto",
    9: "setembro", 10: "outubro",  11: "novembro", 12: "dezembro",
}


@router.get(
    "/{geracao_id}",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Relatório PDF do locador"},
        401: {"description": "Token inválido ou ausente"},
        404: {"description": "Geração não encontrada"},
    },
)
def baixar_pdf(
    geracao_id: UUID,
    current_user: User = Depends(get_user),
    session: Session = Depends(get_session),
) -> Response:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geração não encontrada ou sem permissão de acesso.",
        )

    contrato = session.get(Contrato, geracao.contrato_id)
    if not contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato associado à geração não encontrado.",
        )

    locador_name = _resolve_locador(geracao, current_user, session)
    mes_ref = f"{_MESES[geracao.periodo_ref.month]}/{geracao.periodo_ref.year}"
    filename = f"solarize_{geracao.periodo_ref.strftime('%Y-%m')}.pdf"
    try:
        dados = DadosPDF(
            locador=locador_name,
            mes_ref=mes_ref,
            energia_kwh=Decimal(str(geracao.energia_kwh)),
            tarifa_kwh=Decimal(str(contrato.value_kwh)),
            percentual_locador=Decimal(str(contrato.percentual_locador or 0)),
            desconto_scee=_DESCONTO_SCEE,
            hash_sha256=geracao.hash_sha256,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")
    return Response(
        content=gerar_pdf(dados),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _resolve_locador(geracao: GeracaoEnergia, current_user: User, session: Session) -> str:
    if geracao.created_by:
        creator = session.get(User, geracao.created_by)
        if creator:
            return creator.name
    return current_user.name
