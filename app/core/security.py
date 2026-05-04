from passlib.context import CryptContext

hash_config = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

def create_hash_password(password: str) -> str:
    return hash_config.hash(password)

def verify_hash_password(password: str, db_hash: str) -> bool:
    return hash_config.verify(password, db_hash)

def create_token(data: dict) -> str:
    return "A Fazer"