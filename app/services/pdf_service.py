from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Paleta Solarize ────────────────────────────────────────────────────────────
_G_DARK   = colors.HexColor("#145A32")   # verde escuro  — header, total
_G_MED    = colors.HexColor("#1E8449")   # verde médio   — bordas, destaques
_G_BRIGHT = colors.HexColor("#27AE60")   # verde vivo    — acento
_G_SOFT   = colors.HexColor("#A9DFBF")   # verde suave   — bordas leves
_G_LIGHT  = colors.HexColor("#EAFAF1")   # verde claro   — fundo alternado
_G_PALE   = colors.HexColor("#F0FFF4")   # verde palido  — fundo cards
_SOLAR    = colors.HexColor("#F9A825")   # amarelo solar — badge
_WHITE    = colors.white
_TEXT     = colors.HexColor("#1C2833")
_MUTED    = colors.HexColor("#717D7E")
_BORDER   = colors.HexColor("#D5F5E3")

_QUANT_BRL = Decimal("0.01")
_W         = A4[0] - 4 * cm   # largura útil (A4 com 2 cm de margem em cada lado)


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

    ts = datetime.now(timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")

    buffer = BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    ).build([
        _header(),
        Spacer(1, .55*cm),
        _info_cards(dados),
        Spacer(1, .5*cm),
        _label("DEMONSTRATIVO DE GERAÇÃO"),
        Spacer(1, .12*cm),
        _calc_table(dados, valor),
        Spacer(1, .45*cm),
        _label("FÓRMULA APLICADA"),
        Spacer(1, .12*cm),
        _formula_box(dados, valor),
        Spacer(1, .45*cm),
        _label("HASH DE INTEGRIDADE SHA-256"),
        Spacer(1, .12*cm),
        _hash_box(dados),
        Spacer(1, .7*cm),
        HRFlowable(_W, thickness=1, color=_G_SOFT, spaceAfter=0),
        Spacer(1, .2*cm),
        _footer(ts),
    ])
    return buffer.getvalue()


# ── Blocos ─────────────────────────────────────────────────────────────────────

def _header() -> Table:
    """Banner verde escuro com badge solar amarelo."""
    brand = Paragraph(
        '<font size="26" color="white"><b>SOLARIZE</b></font><br/>'
        '<font size="9" color="#A9DFBF">Sistema de Gestão de Energia Solar</font>',
        ParagraphStyle("hbrand", leading=34),
    )
    badge = Paragraph(
        '<b>Relatório de<br/>Geração Mensal</b>',
        ParagraphStyle("hbadge", fontName="Helvetica-Bold", fontSize=9,
                       textColor=_G_DARK, alignment=TA_CENTER, leading=14),
    )
    t = Table(
        [[brand, badge]],
        colWidths=[_W * .72, _W * .28],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _G_DARK),
        ("BACKGROUND",    (1, 0), ( 1,  0), _SOLAR),
        ("TOPPADDING",    (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("LEFTPADDING",   (0, 0), ( 0,  0), 22),
        ("RIGHTPADDING",  (0, 0), ( 0,  0), 12),
        ("LEFTPADDING",   (1, 0), ( 1,  0), 8),
        ("RIGHTPADDING",  (1, 0), ( 1,  0), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, -1), 4, _SOLAR),
    ]))
    return t


def _info_cards(dados: DadosPDF) -> Table:
    """Dois cards lado a lado: locador e período."""
    s = ParagraphStyle("ic", fontName="Helvetica", fontSize=12,
                       textColor=_TEXT, leading=19)
    locador = Paragraph(
        f'<font size="7" color="#717D7E">LOCADOR</font><br/>'
        f'<b>{dados.locador}</b>',
        s,
    )
    periodo = Paragraph(
        f'<font size="7" color="#717D7E">PERÍODO DE REFERÊNCIA</font><br/>'
        f'<b>{dados.mes_ref.upper()}</b>',
        s,
    )
    t = Table([[locador, periodo]], colWidths=[_W * .5, _W * .5])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _G_PALE),
        ("BOX",           (0, 0), (-1, -1), 1.5, _G_SOFT),
        ("LINEBEFORE",    (0, 0), ( 0, -1), 4,   _G_BRIGHT),
        ("LINEAFTER",     (0, 0), ( 0, -1), 1,   _G_SOFT),
        ("TOPPADDING",    (0, 0), (-1, -1), 15),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _label(text: str) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle("lbl", fontName="Helvetica-Bold", fontSize=8,
                       textColor=_G_MED),
    )


def _calc_table(dados: DadosPDF, valor: Decimal) -> Table:
    hs  = ParagraphStyle("ch",  fontName="Helvetica-Bold", fontSize=10, textColor=_WHITE)
    hr  = ParagraphStyle("chr", fontName="Helvetica-Bold", fontSize=10, textColor=_WHITE,  alignment=TA_RIGHT)
    rs  = ParagraphStyle("cr",  fontName="Helvetica",      fontSize=10, textColor=_TEXT)
    rr  = ParagraphStyle("crr", fontName="Helvetica",      fontSize=10, textColor=_TEXT,   alignment=TA_RIGHT)
    tl  = ParagraphStyle("ctl", fontName="Helvetica-Bold", fontSize=11, textColor=_WHITE)
    tr  = ParagraphStyle("ctr", fontName="Helvetica-Bold", fontSize=14, textColor=_WHITE,  alignment=TA_RIGHT)

    rows = [
        [Paragraph("Descrição", hs),             Paragraph("Valor", hr)],
        [Paragraph("Energia gerada", rs),         Paragraph(f"{dados.energia_kwh:,.0f} kWh", rr)],
        [Paragraph("Tarifa vigente", rs),         Paragraph(f"R$ {dados.tarifa_kwh:.4f}/kWh", rr)],
        [Paragraph("Percentual do locador", rs),  Paragraph(f"{dados.percentual_locador * 100:.1f}%", rr)],
        [Paragraph("Desconto SCEE / Fio B", rs),  Paragraph(f"{dados.desconto_scee * 100:.0f}%", rr)],
        [Paragraph("VALOR A RECEBER", tl),        Paragraph(f"R$ {valor:,.2f}", tr)],
    ]
    t = Table(rows, colWidths=[_W * .65, _W * .35])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,  0), (-1,  0), _G_DARK),
        ("ROWBACKGROUNDS", (0,  1), (-1, -2), [_WHITE, _G_LIGHT]),
        ("BACKGROUND",     (0, -1), (-1, -1), _G_MED),
        ("BOX",            (0,  0), (-1, -1), 1.5, _G_SOFT),
        ("LINEBELOW",      (0,  0), (-1,  0), 0.5, _G_MED),
        ("INNERGRID",      (0,  1), (-1, -2), 0.5, _BORDER),
        ("LINEABOVE",      (0, -1), (-1, -1), 1.5, _G_DARK),
        ("TOPPADDING",     (0,  0), (-1,  0), 11),
        ("BOTTOMPADDING",  (0,  0), (-1,  0), 11),
        ("TOPPADDING",     (0,  1), (-1, -2), 10),
        ("BOTTOMPADDING",  (0,  1), (-1, -2), 10),
        ("TOPPADDING",     (0, -1), (-1, -1), 14),
        ("BOTTOMPADDING",  (0, -1), (-1, -1), 14),
        ("LEFTPADDING",    (0,  0), (-1, -1), 14),
        ("RIGHTPADDING",   (0,  0), (-1, -1), 14),
        ("VALIGN",         (0,  0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _formula_box(dados: DadosPDF, valor: Decimal) -> Table:
    formula = (
        f"{dados.energia_kwh:,.0f} kWh"
        f"  ×  R$ {dados.tarifa_kwh:.4f}"
        f"  ×  {dados.percentual_locador * 100:.1f}%"
        f"  ×  {dados.desconto_scee * 100:.0f}%"
        f"  =  <b>R$ {valor:,.2f}</b>"
    )
    t = Table(
        [[Paragraph(formula, ParagraphStyle("fp", fontName="Helvetica",
                                            fontSize=10, textColor=_TEXT))]],
        colWidths=[_W],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _G_PALE),
        ("BOX",           (0, 0), (-1, -1), 1,   _G_SOFT),
        ("LINEBEFORE",    (0, 0), ( 0, -1), 4,   _G_BRIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 13),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
    ]))
    return t


def _hash_box(dados: DadosPDF) -> Table:
    rows = [
        [Paragraph(dados.hash_sha256,
                   ParagraphStyle("hv", fontName="Courier", fontSize=8,
                                  textColor=_TEXT, wordWrap="CJK"))],
        [Paragraph(
            "Este hash garante a integridade do registro. "
            "Qualquer alteração nos dados invalida a cadeia.",
            ParagraphStyle("hn", fontName="Helvetica-Oblique", fontSize=8,
                           textColor=_MUTED),
        )],
    ]
    t = Table(rows, colWidths=[_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), _G_PALE),
        ("BACKGROUND",    (0, 1), (-1, -1), _WHITE),
        ("BOX",           (0, 0), (-1, -1), 1,   _G_SOFT),
        ("LINEBEFORE",    (0, 0), ( 0, -1), 3,   _G_MED),
        ("TOPPADDING",    (0, 0), (-1,  0), 11),
        ("BOTTOMPADDING", (0, 0), (-1,  0), 11),
        ("TOPPADDING",    (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 11),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    return t


def _footer(ts: str) -> Paragraph:
    return Paragraph(
        f"Gerado em {ts}  ·  Solarize — Sistema de Gestão de Energia Solar",
        ParagraphStyle("ft", fontName="Helvetica", fontSize=8,
                       textColor=_MUTED, alignment=TA_CENTER),
    )
