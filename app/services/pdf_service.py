from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_LOGO_PATH = Path(__file__).parent.parent.parent / "images" / "LogoSolarize.png"

# ── Paleta Solarize ────────────────────────────────────────────────────────────
_G_SECTION = colors.HexColor("#7AA07A")   # verde — barra de seção
_G_LINE    = colors.HexColor("#5A8C5A")   # verde — linha separadora do header
_G_LABEL   = colors.HexColor("#EEF7EE")   # verde palido — labels / cards
_WHITE     = colors.white
_TEXT      = colors.HexColor("#2C2C2C")
_MUTED     = colors.HexColor("#888888")
_BORDER    = colors.HexColor("#C8D8C8")   # borda cinza-verde

_QUANT_BRL = Decimal("0.01")
_W         = A4[0] - 4 * cm   # largura útil (2 cm margem cada lado)
_GAP       = 0.4 * cm         # espaço entre os dois cards


@dataclass(frozen=True)
class DadosPDF:
    locador: str
    locatario: str
    inicio_contrato: date
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

    story = [
        _logo(),
        Spacer(1, .25 * cm),
        HRFlowable(_W, thickness=2, color=_G_LINE, spaceAfter=0),
        Spacer(1, .2 * cm),
        _page_title(),
        Spacer(1, .5 * cm),
        _section_header("Dados do Contrato"),
        Spacer(1, .15 * cm),
        _dados_table(dados, valor),
        Spacer(1, .45 * cm),
        _section_header("Cálculo parcela"),
        Spacer(1, .15 * cm),
        _calculo_cards(valor),
        Spacer(1, .45 * cm),
        _section_header("Hash de integridade SHA-256"),
        Spacer(1, .15 * cm),
        _hash_box(dados),
        Spacer(1, .6 * cm),
        HRFlowable(_W, thickness=0.5, color=_BORDER, spaceAfter=0),
        Spacer(1, .2 * cm),
        _footer(ts),
    ]

    buffer = BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    ).build(story)
    return buffer.getvalue()


# ── Blocos ─────────────────────────────────────────────────────────────────────

def _logo() -> Image:
    # 151×75 px → ratio 2.013 : 1
    img = Image(str(_LOGO_PATH), width=3.0*cm, height=1.49*cm)
    img.hAlign = "LEFT"
    return img


def _page_title() -> Paragraph:
    return Paragraph(
        "PDF de autenticação",
        ParagraphStyle("ptitle", fontName="Helvetica", fontSize=17,
                       textColor=_TEXT, alignment=TA_CENTER, leading=22),
    )


def _section_header(text: str) -> Table:
    t = Table(
        [[Paragraph(text, ParagraphStyle("sh", fontName="Helvetica-Bold",
                                         fontSize=11, textColor=_WHITE))]],
        colWidths=[_W],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _G_SECTION),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    return t


def _dados_table(dados: DadosPDF, valor: Decimal) -> Table:
    lb = ParagraphStyle("lb", fontName="Helvetica-Bold", fontSize=10, textColor=_TEXT)
    vl = ParagraphStyle("vl", fontName="Helvetica",      fontSize=10, textColor=_TEXT)

    def _fmt_kwh(v: Decimal) -> str:
        return f"{int(v):,}".replace(",", ".") + " kWh"

    rows = [
        [Paragraph("Locador:",                 lb), Paragraph(dados.locador,                              vl)],
        [Paragraph("Locatário:",               lb), Paragraph(dados.locatario,                            vl)],
        [Paragraph("Energia gerada:",          lb), Paragraph(_fmt_kwh(dados.energia_kwh),                vl)],
        [Paragraph("Tarifa vigente:",          lb), Paragraph(f"R$ {dados.tarifa_kwh:.4f}/kWh",           vl)],
        [Paragraph("Percentual do locador:",   lb), Paragraph(f"{dados.percentual_locador * 100:.1f}%",   vl)],
        [Paragraph("Desconto SCEE / Fio B:",   lb), Paragraph(f"{dados.desconto_scee * 100:.0f}%",        vl)],
        [Paragraph("Início do contrato:",      lb), Paragraph(dados.inicio_contrato.strftime("%d/%m/%Y"), vl)],
        [Paragraph("Valor a receber",          lb), Paragraph(f" R$ {valor:,.2f}",                        vl)],
    ]

    t = Table(rows, colWidths=[_W * 0.40, _W * 0.60])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,  0), (0, -1), _G_LABEL),
        ("BACKGROUND",    (1,  0), (1, -1), _WHITE),
        ("BOX",           (0,  0), (-1, -1), 1,   _BORDER),
        ("INNERGRID",     (0,  0), (-1, -1), 0.5, _BORDER),
        ("TOPPADDING",    (0,  0), (-1, -1), 9),
        ("BOTTOMPADDING", (0,  0), (-1, -1), 9),
        ("LEFTPADDING",   (0,  0), (-1, -1), 12),
        ("RIGHTPADDING",  (0,  0), (-1, -1), 12),
        ("VALIGN",        (0,  0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _left_formula_card(width: float) -> Table:
    title_s   = ParagraphStyle("lct", fontName="Helvetica-Bold", fontSize=10, textColor=_TEXT)
    formula_s = ParagraphStyle("pf",  fontName="Helvetica",      fontSize=9,  textColor=_TEXT, leading=16)
    note_s    = ParagraphStyle("pn",  fontName="Helvetica-Oblique", fontSize=8, textColor=_MUTED, leading=12)

    card = Table(
        [[Paragraph("Fórmula aplicada", title_s)],
         [Spacer(1, 0.25 * cm)],
         [Paragraph("Valor = E × T × P × (1 − D)", formula_s)],
         [Spacer(1, 0.1 * cm)],
         [Paragraph("E = energia gerada (kWh)  ·  T = tarifa (R$/kWh)", note_s)],
         [Paragraph("P = percentual do locador  ·  D = desconto SCEE (5%)", note_s)]],
        colWidths=[width],
    )
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _G_LABEL),
        ("BOX",           (0, 0), (-1, -1), 1, _BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _right_value_card(valor: Decimal, width: float) -> Table:
    title_s = ParagraphStyle("rct", fontName="Helvetica-Bold", fontSize=10, textColor=_TEXT)
    val_s   = ParagraphStyle("rcv", fontName="Helvetica-Bold", fontSize=24,
                              textColor=_TEXT, alignment=TA_CENTER, leading=30)

    card = Table(
        [[Paragraph("Valor da parcela", title_s)],
         [Spacer(1, 0.3 * cm)],
         [Paragraph(f"R$ {valor:,.2f}", val_s)]],
        colWidths=[width],
    )
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _G_LABEL),
        ("BOX",           (0, 0), (-1, -1), 1, _BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _calculo_cards(valor: Decimal) -> Table:
    card_w = (_W - _GAP) / 2
    left  = _left_formula_card(card_w)
    right = _right_value_card(valor, card_w)

    t = Table(
        [[left, "", right]],
        colWidths=[card_w, _GAP, card_w],
    )
    t.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


def _hash_box(dados: DadosPDF) -> Table:
    hash_s = ParagraphStyle("hv", fontName="Courier", fontSize=8,
                            textColor=_TEXT, wordWrap="CJK", alignment=TA_CENTER)
    note_s = ParagraphStyle("hn", fontName="Helvetica-Oblique", fontSize=8,
                            textColor=_MUTED, alignment=TA_CENTER)
    rows = [
        [Paragraph(dados.hash_sha256, hash_s)],
        [Paragraph(
            "Esse hash garante a integridade do registro. "
            "Qualquer alteração nos dados invalida o cadastro",
            note_s,
        )],
    ]
    t = Table(rows, colWidths=[_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), _G_LABEL),
        ("BACKGROUND",    (0, 1), (-1, -1), _WHITE),
        ("BOX",           (0, 0), (-1,  0), 1, _BORDER),
        ("TOPPADDING",    (0, 0), (-1,  0), 14),
        ("BOTTOMPADDING", (0, 0), (-1,  0), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
    ]))
    return t


def _footer(ts: str) -> Paragraph:
    return Paragraph(
        f"Gerado em {ts} - Solarize - Sistema de Gestão de Energia Solar",
        ParagraphStyle("ft", fontName="Helvetica", fontSize=8,
                       textColor=_MUTED, alignment=TA_CENTER),
    )
