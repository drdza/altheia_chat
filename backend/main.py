# backend/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.logging import configure_logging
from routers import chat, admin, health, auth
from services.db import init_db


configure_logging()

# 🔹 Inicializa la base de datos al arrancar el backend
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="AltheIA RAG Service", version="1.0", lifespan=lifespan)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])