from sqlmodel import create_engine, Session
from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

_pool_kwargs: dict = {"pool_pre_ping": True}
if not _is_sqlite:
    _pool_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

engine = create_engine(settings.database_url, **_pool_kwargs)


def get_session():
    with Session(engine) as session:
        yield session
