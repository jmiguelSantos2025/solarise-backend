import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class Register_Request(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(examples=["john.doe@contact.com"])
    password: str = Field(min_length=8, examples=["Password0@$"])
    role: str = Field(examples=["Administrator", "Analyst"])
    org_name: str = Field(min_length=2, max_length=255, examples=["Solarize Energia"])
    org_cnpj: str = Field(min_length=14, max_length=18, examples=["12.345.678/0001-99"])
    org_email: EmailStr = Field(examples=["contato@solarize.com"])

    @field_validator("password")
    @classmethod
    def password_validator(cls, password: str) -> str:
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if re.search(pattern, password):
            return password
        raise ValueError("A senha deve conter maiúscula, minúscula, número e caractere especial (@$!%*?&).")


class User_Response(BaseModel):
    ID: str
    name: str
    email: str
    org_id: str
    role: str
    model_config = {"from_attributes": True}


class Token_Response(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class Message_Response(BaseModel):
    message: str
    success: bool = True
