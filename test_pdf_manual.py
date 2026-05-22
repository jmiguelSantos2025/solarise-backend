from datetime import date
from decimal import Decimal
from app.services.pdf_service import DadosPDF, gerar_pdf

dados = DadosPDF(
    locador="Energia Solar LTDA",
    locatario="Bernardo Souza",
    inicio_contrato=date(2024, 4, 24),
    energia_kwh=Decimal("1000"),
    tarifa_kwh=Decimal("1.0000"),
    percentual_locador=Decimal("1.00"),
    desconto_scee=Decimal("0.95"),
    hash_sha256="47308257238688934579837547308257238693457983754730825723869345798375",
)

with open("teste_solarize.pdf", "wb") as f:
    f.write(gerar_pdf(dados))

print("PDF gerado: teste_solarize.pdf")
