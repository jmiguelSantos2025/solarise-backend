from decimal import Decimal
from app.services.pdf_service import DadosPDF, gerar_pdf

dados = DadosPDF(
    locador="Joao Silva",
    mes_ref="marco/2026",
    energia_kwh=Decimal("38500"),
    tarifa_kwh=Decimal("0.85"),
    percentual_locador=Decimal("0.30"),
    desconto_scee=Decimal("0.95"),
    hash_sha256="a3f8c2e1d4b7f9a0e2c5d8b1f4a7c0e3d6b9f2a5c8e1d4b7f0a3c6e9d2b5f8a1",
)

with open("teste_solarize.pdf", "wb") as f:
    f.write(gerar_pdf(dados))

print("PDF gerado: teste_solarize.pdf")
