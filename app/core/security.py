from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import settings

hash_config = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

def create_hash_password(password: str) -> str: #Done!
    return hash_config.hash(password)

def verify_hash_password(password: str, db_hash: str) -> bool: #Done!
    return hash_config.verify(password, db_hash)

def create_token(data: dict, expire: int = 24) -> str: #Done!
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=expire)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> dict | None: #Done!
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None