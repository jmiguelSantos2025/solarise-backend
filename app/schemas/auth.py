from pydantic import BaseModel, EmailStr, Field, field_validator
import re, uuid

class Register_Request(BaseModel):
    ID: uuid.UUID = Field(default_factory=uuid.uuid7)
    name: str = Field(
        min_length=2,
        max_length=100,
        examples=["SolarTech", "Energy COM"],
        )
    email: EmailStr = Field(
        examples=["contact@solartech.com", "contact@energycom.com"],
    )
    password: str = Field(
        min_length=8,
        examples=["Password123@$", "K&bt7T4m!@3bs*"],
        description="The password must have 8 characters, special symbols, numbers and lower and upper case letras"
    )
    role: str = Field(
        examples=["Administrator", "Analyst"]
    )

    @field_validator("password")
    @classmethod
    def password_validator(cls, password):
        comparator = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if re.search(comparator, password):
            return password
        return False

class Login_Request(BaseModel):
    email: EmailStr = Field(
        examples=["contact@solartech.com", "contact@energycom.com"]
    )
    password: str = Field(
        examples=["Password123@$"]
    )

class Invite_Request(BaseModel):
    name: str = Field(
        examples=["John", "Jane"]
    )
    email: EmailStr = Field(
        examples=["john@gmail.com", "jane@gmail.com"],
    )

class Refresh_Request(BaseModel):
    refresh_token: str = Field(
        examples=["NYvt238B92j2HF27jG12H1kd03..."]
    )



class User_Response(BaseModel):
    ID: int
    name: str
    email: str
    org_id: str
    role: str

class Token_Response(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class Message_Response(BaseModel):
    message: str
    sucess: bool = True