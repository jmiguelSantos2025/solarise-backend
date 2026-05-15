from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from uuid import UUID

class ContratoCreate(BaseModel):
    numero: str
    decricao: str | None = None
    data_inicio: date
    data_fim: date | None = None
    percentual_locador: Decimal
    tarifa_kwh: Decimal

class ContratoRead(ContratoCreate):
    id: UUID
    org_id: UUID
    class Config:
        from_attributes = True
