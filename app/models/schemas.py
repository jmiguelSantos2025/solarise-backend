from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import Optional

class ContratoCreate(BaseModel):
    number: str
    description: Optional[str] = None
    start_date: date
    end_date: date | None = None
    percentual_locador: Decimal
    value_kwh: Decimal

class ContratoRead(ContratoCreate):
    id: UUID
    organization_id: UUID
    class Config:
        from_attributes = True
