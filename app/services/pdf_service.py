from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_NAVY = colors.HexColor("#1A5276")
_MINT = colors.HexColor("#D1F2EB")
_QUANT_BRL = Decimal("0.01")
_LOSS_FACTOR = Decimal("0.95")


@dataclass(frozen=True)
class DadosPDF:
    locador: str
    mes_ref: str
    energia_kwh: Decimal
    tarifa_kwh: Decimal
    percentual_locador: Decimal
    desconto_scee: Decimal
    hash_sha256: str


def gerar_pdf(dados: DadosPDF) -> bytes:
    valor = (
        dados.energia_kwh
        * dados.tarifa_kwh
        * dados.percentual_locador
        * dados.desconto_scee
    ).quantize(_QUANT_BRL, rounding=ROUND_HALF_UP)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    hash_style = ParagraphStyle(
        "hash",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        wordWrap="CJK",
    )

    story = [
        Paragraph("<b>SOLARIZE</b>", styles["Title"]),
        Paragraph("Relatório de Geração de Energia", styles["Heading2"]),
        Spacer(1, 0.4 * cm),
        Paragraph(f"Locador: <b>{dados.locador}</b>", styles["Normal"]),
        Paragraph(f"Período de referência: <b>{dados.mes_ref}</b>", styles["Normal"]),
        Spacer(1, 0.4 * cm),
        _build_table(dados, valor),
        Spacer(1, 0.6 * cm),
        Paragraph("<b>Fórmula aplicada:</b>", styles["Heading3"]),
        Paragraph(_build_formula(dados, valor), styles["Normal"]),
        Spacer(1, 0.8 * cm),
        Paragraph("<b>Hash de integridade SHA-256:</b>", styles["Heading3"]),
        Paragraph(dados.hash_sha256, hash_style),
        Spacer(1, 0.3 * cm),
        Paragraph(
            "Este hash garante a integridade do registro. "
            "Qualquer alteração nos dados invalida a cadeia.",
            styles["Normal"],
        ),
    ]

    doc.build(story)
    return buffer.getvalue()


def _build_table(dados: DadosPDF, valor: Decimal) -> Table:
    rows = [
        ["Descrição", "Valor"],
        ["Energia gerada", f"{dados.energia_kwh:,.0f} kWh"],
        ["Tarifa vigente", f"R$ {dados.tarifa_kwh:.4f}/kWh"],
        ["Percentual do locador", f"{dados.percentual_locador * 100:.1f}%"],
        ["Desconto SCEE/Fio B", f"{dados.desconto_scee * 100:.0f}%"],
        ["VALOR A RECEBER", f"R$ {valor:,.2f}"],
    ]

    table = Table(rows, colWidths=[10 * cm, 5 * cm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND",    (0, 0),  (-1, 0),  _NAVY),
            ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
            ("BACKGROUND",    (0, -1), (-1, -1), _MINT),
            ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID",          (0, 0),  (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.white]),
            ("ALIGN",         (1, 1),  (-1, -1), "RIGHT"),
        ])
    )
    return table


def _build_formula(dados: DadosPDF, valor: Decimal) -> str:
    return (
        f"Valor = {dados.energia_kwh:,.0f} kWh"
        f" × R$ {dados.tarifa_kwh:.4f}"
        f" × {dados.percentual_locador * 100:.1f}%"
        f" × {dados.desconto_scee * 100:.0f}%"
        f" = R$ {valor:,.2f}"
    )
