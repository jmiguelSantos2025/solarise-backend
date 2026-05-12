import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.schemas.auth import *
from app.core.security import *

router = APIRouter()
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

users: dict = {}

def get_user(token: str = Depends(oauth2)) -> dict: #Done!
    data = verify_token(token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if "ID" not in data:
        raise HTTPException(status_code=401, detail="Malformed token.")
    return data

@router.post("/register", response_model=Message_Response)
def register(user: Register_Request): #Done!
    if user.email in users:
        raise HTTPException(status_code=409, detail="Email already registered.")
    
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    try:
        hashed_password = create_hash_password(user.password)
        users[user.email] = {
            "ID": user_id,
            "name": user.name,
            "email": user.email,
            "password_hash": hashed_password,
            "org_id": org_id,
            "role": user.role
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error")

    return Message_Response(message=f"Installer {user.name} registered sucessfully", success=True)
    
@router.post("/login", response_model=Token_Response)
def login(user: OAuth2PasswordRequestForm = Depends()): #Done!

    user_data = users.get(user.username)

    if not user_data :
        raise HTTPException(status_code=401, detail="User not found")
    if not verify_hash_password(user.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    try:
        payload = {
            "name": user_data["name"],
            "ID": user_data["ID"],
            "org_id": user_data["org_id"],
            "role": user_data["role"]
        }
    except:
        raise HTTPException(status_code=500, detail="Error")

    return Token_Response(
        access_token=create_token(payload, 24),
        refresh_token=create_token({**payload, "type": "refresh"}, 168),
        token_type="bearer",
        expires_in=86400
    )

@router.get("/profile", response_model=User_Response)
def profile(current_user: dict = Depends(get_user)):

    target_ID = current_user.get("ID")

    if not target_ID:
        raise HTTPException(status_code=401, detail="Token payload missing ID")

    for user in users.values():
        if user["ID"] == target_ID:
            return User_Response(
                ID=user["ID"],
                name=user["name"],
                email=user["email"],
                org_id=user["org_id"],
                role=user["role"]
            )
    raise HTTPException(status_code=404, detail="User not found.")