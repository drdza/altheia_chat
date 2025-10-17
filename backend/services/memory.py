# backend/services/memory.py

import os, json, redis.asyncio as redis
from core.config import settings

REDIS_URL = settings.REDIS_URL

# 🧠 Conexión global
redis_client = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_keepalive=True,
        retry_on_timeout=True,
        socket_connect_timeout=5,      # Timeout de conexión
        socket_timeout=5,              # Timeout de operaciones
        health_check_interval=30       # Health check cada 30s
)

async def save_message(chat_id: str, role: str, content: str, limit: int = 10):
    """
    Guarda un mensaje en el historial de Redis y mantiene solo los últimos N.
    """
    entry = json.dumps({"role": role, "content": content})
    key = f"chat:{chat_id}:history"
    await redis_client.rpush(key, entry)
    await redis_client.ltrim(key, -limit, -1)

async def get_history(chat_id: str):
    """
    Recupera la conversación reciente desde Redis.
    """
    key = f"chat:{chat_id}:history"
    messages = await redis_client.lrange(key, 0, -1)
    return [json.loads(m) for m in messages]

async def clear_history(chat_id: str):
    """
    Limpia la memoria temporal de un chat.
    """
    await redis_client.delete(f"chat:{chat_id}:history")
