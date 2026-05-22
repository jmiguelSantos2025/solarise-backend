from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


<<<<<<< HEAD
class ContractCreate(BaseModel):
    number: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    landlord_percentage: Decimal
    value: Decimal
=======
class ContratoCreate(BaseModel):
    number: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    percentual_locador: Decimal = Field(gt=0, le=1)
    value_kwh: Decimal = Field(gt=0)
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7


class ContractRead(ContractCreate):
    id: UUID
<<<<<<< HEAD
    org_id: UUID
=======
    organization_id: UUID
    status: str
    created_at: datetime
>>>>>>> f1f4f9fccb3164ad566b3f1b97b0e4299cf84fc7
    model_config = ConfigDict(from_attributes=True)
