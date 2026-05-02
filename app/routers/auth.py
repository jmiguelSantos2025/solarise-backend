from fastapi import APIRouter
from pydantic import EmailStr
from app.schemas import auth

users = {}

router = APIRouter()

@router.post("/register")
def register_profile(ID: int, profile: auth.User_Register):
    if ID in users:
        return {"Error": "User ID already exists"}
    else:
        users[ID] = profile
        return {"Sucess": "User registered"}
    
@router.post("/login")
def login_profile(email: EmailStr, hash_password: str):
    for user_id, user in users.items():
        if user.email == email:
            if user.hash_password == hash_password:
                return {
                    "success": "Login successful",
                    "user_id": user_id
                }
            return {"error": "Invalid password"}

    return {"error": "User not found"}
@router.get("/me")
def get_profile(ID: int):
    if ID in users:
        return users[ID]
    else:
        return {"Error": "User ID doesn't exists"}