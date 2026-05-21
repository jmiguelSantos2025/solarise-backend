from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContractCreate(BaseModel):
    number: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    landlord_percentage: Decimal
    value: Decimal


class ContractRead(ContractCreate):
    id: UUID
    org_id: UUID
    model_config = ConfigDict(from_attributes=True)
