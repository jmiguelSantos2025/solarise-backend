from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContractCreate(BaseModel):
    number: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    landlord_percentage: Decimal
    value_kwh: Decimal


class ContractRead(ContractCreate):
    id: UUID
    organization_id: UUID
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
