# app/routers/health.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/live")
def live():
    return {"status": "ok"}

@router.get("/ready")
def ready():
    return {"status": "ready"}
