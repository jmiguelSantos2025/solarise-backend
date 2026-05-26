from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PreviewRequest(BaseModel):
    contract_id: str = Field(examples=["ctrt-001"])
    generated_energy: Decimal = Field(gt=0, examples=["1000.0"])
    date: datetime = Field(examples=["2026-03-01T00:00:00"])


class GenerationRequest(BaseModel):
    contract_id: str = Field(examples=["ctrt-001"])
    generated_energy: Decimal = Field(gt=0, examples=["1000.0"])
    date: datetime = Field(examples=["2026-03-01T00:00:00"])


class PreviewResponse(BaseModel):
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
