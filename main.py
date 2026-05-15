from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from sqlmodel import SQLModel
from app.routers import auth, generation
import contratos
import dashboard

app = FastAPI(title="Solarize API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(generation.router, prefix="/generation", tags=["generation"])
app.include_router(contratos.router)
app.include_router(dashboard.router)

@app.get("/health")
def health():
    return {"status": "OK"}