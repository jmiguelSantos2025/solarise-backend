from fastapi import APIRouter
from app.schemas.auth import *

users = {}

router = APIRouter()

@router.post("/register")
def register_profile(profile: Register_Request):
    if profile.ID in users or {"email": profile.email} in users.values() or {"password": profile.password} in users.values():
        return {"Error": "User already exists"}
    else:
        users[profile.ID] = profile
        return {"Sucess": "User registered"}
    
@router.post("/login")
def login_profile(profile: Login_Request):
    for user_id, user in users.items():
        if user.email == profile.email:
            if user.password == profile.password:
                return {
                    "success": "Login successful",
                    "Welcome": users[user_id].name
                }
            return {"Error": "Invalid password"}
    return {"Error": "User not found"}