from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.routers import auth, generation
from app.models import contratos, dashboard
from app.core.config import settings
from database.database import engine

app = FastAPI(title="Solarise API", summary="Documentação sobre o funcionamento da API oficial do projeto Solarise")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(generation.router, prefix="/generation", tags=["Generation"])
app.include_router(contratos.router)
app.include_router(dashboard.router)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/health")
def server():
    return {"Status": "OK", "Version": 1.0}

