from pydantic import BaseModel, EmailStr

class Dashboard_Preview(BaseModel):
    org_id: int