from pydantic import BaseModel
from datetime import datetime

class Preview_Request(BaseModel):
    contract_ID: str
    generated_energy: float
    date: datetime

class Generation_Request(BaseModel):
    contract_ID: str
    generated_energy: float
    date: datetime


class Preview_Response(BaseModel):
    generated_energy: float
    value: float
    date: datetime

class Generation_Response(BaseModel):
    ID: str
    