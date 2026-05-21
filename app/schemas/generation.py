from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional

class Preview_Request(BaseModel):
    contract_ID: str = Field(examples=["ctrt-001"])
    generated_energy: Decimal = Field(gt=0, examples=["1000.0"])
    date: datetime = Field(examples=["2026-03-01T00:00:00"])

class Generation_Request(BaseModel):
    contract_ID: str = Field(examples=["ctrt-001"])
    generated_energy: Decimal = Field(gt=0, examples=["1000.0"])
    date: datetime = Field(examples=["2026-03-01T00:00:00"])


class Preview_Response(BaseModel):
    generated_energy: str
    tariff: str
    landlord_percentage: str
    loss_factor: str = "0.95"
    formula: str
    value: str
    date: str
    saved: bool = False

class Generation_Response(BaseModel):
    ID: str
    contract_ID: str
    value: Decimal
    hash_sha256: str
    previous_hash: Optional[str] = None
    date: datetime