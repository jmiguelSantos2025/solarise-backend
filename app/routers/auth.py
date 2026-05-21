import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.security import create_hash_password, create_token, verify_hash_password, verify_token
from app.schemas.auth import Message_Response, Register_Request, Token_Response, User_Response
from database.database import get_session
from database.models import Organization, User

router = APIRouter()
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user(token: str = Depends(oauth2), session: Session = Depends(get_session)) -> User:
    data = verify_token(token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = data.get("ID")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")
    user = session.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


@router.post("/register", response_model=Message_Response)
def register(payload: Register_Request, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    org = session.exec(select(Organization).where(Organization.cnpj == payload.org_cnpj)).first()
    if not org:
        org = Organization(name=payload.org_name, cnpj=payload.org_cnpj, email=payload.org_email)
        session.add(org)
        session.flush()

    try:
        user = User(
            email=payload.email,
            name=payload.name,
            role=payload.role,
            organization_id=org.id,
            password_hash=create_hash_password(payload.password),
        )
        session.add(user)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuário.",
        ) from exc

    return Message_Response(message=f"Usuário {payload.name} registrado com sucesso.", success=True)


@router.post("/login", response_model=Token_Response)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    # form.username deve ser o e-mail cadastrado, não o nome do usuário
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not user.password_hash or not verify_hash_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    payload = {
        "name": user.name,
        "ID": str(user.id),
        "org_id": str(user.organization_id),
        "role": user.role,
    }
    return Token_Response(
        access_token=create_token(payload, 24),
        refresh_token=create_token({**payload, "type": "refresh"}, 168),
        token_type="bearer",
        expires_in=86400,
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
