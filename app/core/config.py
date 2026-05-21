from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    cors_origins: str = "http://localhost:3000"
    app_env: str = "production"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }

    @field_validator("database_url")
    @classmethod
    def database_url_required(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "DATABASE_URL não configurado. Defina-o no arquivo .env ou como variável de ambiente."
            )
        return v

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_required(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "JWT_SECRET não configurado. Defina-o no arquivo .env ou como variável de ambiente."
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET deve ter no mínimo 32 caracteres.")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Suporta dois formatos no .env:
          CORS_ORIGINS=http://localhost:3000,http://localhost:8080
          CORS_ORIGINS=[http://localhost:3000,http://localhost:8080]
        """
        raw = self.cors_origins.strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        return [o.strip().strip("\"'") for o in raw.split(",") if o.strip()]


settings = Settings()
