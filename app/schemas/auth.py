from pydantic import BaseModel, EmailStr

class User_Register(BaseModel):
    name: str
    email: EmailStr
    hash_password: str

class User_Login(BaseModel):
    email: EmailStr
    hash_password: str