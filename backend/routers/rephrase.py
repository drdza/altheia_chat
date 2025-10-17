from fastapi import APIRouter
from typing import Optional
from core.graph import run_rephrase
from models.schemas import RephraseRequest, RephraseResponse

router = APIRouter()



