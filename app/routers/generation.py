from fastapi import APIRouter
from app.schemas.generation import *

contracts = {}

router = APIRouter()

@router.post("/preview")
def preview_dashboard(item: Preview_Request):
    if item.contract_ID in contracts:
        return contracts[item.contract_ID]
    else:
        return {"Error": "Contract doesn't exists"}

@router.post("/")
def create_contract(item: Preview_Request):
    if item.contract_ID in contracts:
        return {"Error": "Contract already exists"}
    else:
        contracts[item.contract_ID] = item
        return {"Sucess": "Contract registered"}