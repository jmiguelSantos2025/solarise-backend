# fix_contrato.py
from sqlmodel import Session, select
from decimal import Decimal
from database.database import engine
from database.models import Contract

with Session(engine) as session:
    contrato = session.exec(select(Contract)).first()
    if contrato:
        contrato.landlord_percentage = Decimal("0.30")
        session.add(contrato)
        session.commit()
        print(f"Contrato {contrato.number} atualizado: landlord_percentage = {contrato.landlord_percentage}")
    else:
        print("Nenhum contrato encontrado")