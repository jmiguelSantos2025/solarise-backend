from fastapi import APIRouter
from pydantic import EmailStr
from app.schemas.generation import Dashboard_Preview

router = APIRouter()

@router.post("/preview")
def preview_dashboar(item: Dashboard_Preview):
    return 