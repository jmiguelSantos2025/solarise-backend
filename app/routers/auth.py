import uuid as _uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_hash_password, create_token, verify_hash_password, verify_token
from app.schemas.auth import Message_Response, Register_Request, Token_Response, User_Response
from database.database import get_session
from database.models import Organization, User

router = APIRouter()

_DEV_EMAIL = "dev@solarize.local"

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_or_create_dev_user(session: Session) -> User:
    real_user = session.exec(
        select(User).where(User.email != _DEV_EMAIL).order_by(User.created_at)
    ).first()
    if real_user:
        return real_user

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
        raise HTTPException(status_code=401, detail="Malformed token.")

    user = session.get(User, _uuid.UUID(data["ID"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


@router.post("/register", response_model=Message_Response, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, payload: Register_Request, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    org = session.exec(select(Organization).where(Organization.cnpj == payload.org_cnpj)).first()
    if not org:
        org = Organization(name=payload.org_name, cnpj=payload.org_cnpj, email=payload.org_email)
        session.add(org)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization CNPJ already registered.")

    user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        organization_id=org.id,
        password_hash=create_hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    return Message_Response(message=f"User {payload.name} registered successfully.", success=True)


@router.post("/login", response_model=Token_Response)
@limiter.limit("5/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not user.password_hash or not verify_hash_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token_payload = {
        "name": user.name,
        "ID": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role,
    }
    expire_hours = settings.jwt_expire_hours
    return Token_Response(
        access_token=create_token(token_payload, expire_hours),
        refresh_token=create_token({**token_payload, "type": "refresh"}, expire_hours * 7),
        token_type="bearer",
        expires_in=expire_hours * 3600,
    )


@router.get("/profile", response_model=User_Response)
def profile(current_user: User = Depends(get_user)):
    return User_Response(
        ID=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        org_id=str(current_user.organization_id),
        role=current_user.role,
    )
