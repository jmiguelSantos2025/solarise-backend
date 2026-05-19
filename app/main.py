from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, generation, pdf_router
from app.models import contratos, dashboard
from app.core.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Em produção, rode `alembic upgrade head` antes de subir a aplicação.
    # create_all é mantido apenas para conveniência em desenvolvimento local.
    from sqlmodel import SQLModel
    from database.database import engine
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Solarise API",
    summary="Documentação sobre o funcionamento da API oficial do projeto Solarise",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(generation.router, prefix="/generation", tags=["Generation"])
app.include_router(pdf_router.router)
app.include_router(contratos.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"Status": "OK", "Version": 1.0}
