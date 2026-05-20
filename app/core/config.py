from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    cors_origins: str = "http://localhost:3000"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }

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
