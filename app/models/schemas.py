from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContratoCreate(BaseModel):
    number: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    percentual_locador: Decimal = Field(gt=0, le=1)
    value_kwh: Decimal = Field(gt=0)


class ContratoRead(ContratoCreate):
    id: UUID
    organization_id: UUID
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
