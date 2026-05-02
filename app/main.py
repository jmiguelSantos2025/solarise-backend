from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, generation

app = FastAPI(title="Solarise API", summary="Documentação sobre o funcionamento da API oficial do projeto Solarise")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(generation.router, prefix="/generation", tags=["Generation"])