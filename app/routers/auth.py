import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_hash_password, create_token, verify_hash_password, verify_token
from app.schemas.auth import Message_Response, Register_Request, Token_Response, User_Response
from database.database import get_session
from database.models import Organization, User

router = APIRouter()

_DEV_EMAIL = "dev@solarize.local"

# auto_error=False permite que token seja None — tratado manualmente abaixo
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_or_create_dev_user(session: Session) -> User:
    # Prefer the first real user so the dev context shares the same org and data
    real_user = session.exec(
        select(User).where(User.email != _DEV_EMAIL).order_by(User.created_at)
    ).first()
    if real_user:
        return real_user

    # No real users yet — fall back to a dedicated dev user
    dev_user = session.exec(select(User).where(User.email == _DEV_EMAIL)).first()
    if dev_user:
        return dev_user

    org = Organization(name="Dev Organization", cnpj="00000000000000", email=_DEV_EMAIL)
    session.add(org)
    session.flush()
    dev_user = User(
        email=_DEV_EMAIL,
        name="Dev User",
        role="admin",
        organization_id=org.id,
        password_hash=create_hash_password("dev"),
    )
    session.add(dev_user)
    session.commit()
    session.refresh(dev_user)
    return dev_user


def get_user(token: Optional[str] = Depends(oauth2), session: Session = Depends(get_session)) -> User:
    if token is None:
        if settings.app_env == "development":
            return _get_or_create_dev_user(session)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    data = verify_token(token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if "ID" not in data:
        raise HTTPException(status_code=401, detail="Error: Malformed token.")
    return data

@router.post("/register", response_model=Message_Response)
def register(user: Register_Request): #Done!
    if user.email in users:
        raise HTTPException(status_code=409, detail="Error : Email already registered.")
    
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

    return Message_Response(message=f"Installer {user.name} registered sucessfully", success=True)
    
@router.post("/login", response_model=Token_Response)
def login(user: OAuth2PasswordRequestForm = Depends()): #Done!

    org = session.exec(select(Organization).where(Organization.cnpj == payload.org_cnpj)).first()
    if not org:
        org = Organization(name=payload.org_name, cnpj=payload.org_cnpj, email=payload.org_email)
        session.add(org)
        session.flush()

    if not user_data :
        raise HTTPException(status_code=401, detail="Error: User not found")
    if not verify_hash_password(user.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Error: Invalid credentials.")
    try:
        payload = {
            "name": user_data["name"],
            "ID": user_data["ID"],
            "org_id": user_data["org_id"],
            "role": user_data["role"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

    return Message_Response(message=f"Usuário {payload.name} registrado com sucesso.", success=True)


@router.post("/login", response_model=Token_Response)
@limiter.limit("5/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not user.password_hash or not verify_hash_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    payload = {
        "name": user.name,
        "ID": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role,
    }
    expire_hours = settings.jwt_expire_hours
    return Token_Response(
        access_token=create_token(payload, expire_hours),
        refresh_token=create_token({**payload, "type": "refresh"}, expire_hours * 7),
        token_type="bearer",
        expires_in=expire_hours * 3600,
    )

@router.get("/profile", response_model=User_Response) #Done!
def profile(current_user: dict = Depends(get_user)):

    target_ID = current_user.get("ID")

    if not target_ID:
        raise HTTPException(status_code=401, detail="Error: Token payload missing ID")

    for user in users.values():
        if user["ID"] == target_ID:
            return User_Response(
                ID=user["ID"],
                name=user["name"],
                email=user["email"],
                org_id=user["org_id"],
                role=user["role"]
            )
    raise HTTPException(status_code=404, detail="Error: User not found.")
