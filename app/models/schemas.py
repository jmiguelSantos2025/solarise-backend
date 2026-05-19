from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContratoCreate(BaseModel):
    number: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    percentual_locador: Decimal
    value_kwh: Decimal


class ContratoRead(ContratoCreate):
    id: UUID
    organization_id: UUID
    model_config = ConfigDict(from_attributes=True)
