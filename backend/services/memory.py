# backend/services/memory.py

import logging, json, redis.asyncio as redis
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

log = logging.getLogger(__name__)

async def save_message(chat_id: str, role: str, content: str, limit: int = 10):
    """
    Guarda un mensaje en el historial de Redis y mantiene solo los últimos N.
    """
    entry = json.dumps({"role": role, "content": content})
    key = f"chat:{chat_id}:history"
    await redis_client.rpush(key, entry)
    await redis_client.ltrim(key, -limit, -1)

async def get_all_history(chat_id: str):
    """
    Recupera la conversación reciente desde Redis.
    """
    key = f"chat:{chat_id}:history"
    all_messages = await redis_client.lrange(key, 0, -1)
    
    messages = [json.loads(m) for m in all_messages]

    log.info(f"All History: {messages}")
    return messages

async def get_optimized_history(chat_id: str, max_messages: int = 8, max_tokens: int = 1200):
    """
    Recupera historial optimizado con límites por mensajes Y tokens.
    """
    try:
        key = f"chat:{chat_id}:history"
        
        # Obtener últimos N mensajes
        messages = await redis_client.lrange(key, -max_messages, -1)
        
        if not messages:
            return []
            
        parsed_messages = [json.loads(m) for m in messages]
        
        # Calcular tokens aproximados (4 tokens por palabra en español)
        total_tokens = 0
        for msg in parsed_messages:
            content = msg.get('content', '')
            total_tokens += len(content.split()) * 4
        
        log.info(f"🧠 Historial para {chat_id}: {len(parsed_messages)} mensajes, ~{total_tokens} tokens")
        
        # Si excede límite de tokens, recortar mensajes más antiguos
        if total_tokens > max_tokens:
            optimized_messages = []
            current_tokens = 0
            
            # Recorrer de más reciente a más antiguo
            for msg in reversed(parsed_messages):
                content = msg.get('content', '')
                msg_tokens = len(content.split()) * 4
                
                # Si agregar este mensaje excede el límite Y ya tenemos algunos mensajes, parar
                if current_tokens + msg_tokens > max_tokens and optimized_messages:
                    break
                    
                optimized_messages.insert(0, msg)  # Mantener orden cronológico
                current_tokens += msg_tokens
            
            log.info(f"🧠 Historial optimizado: {len(optimized_messages)}/{len(parsed_messages)} mensajes, ~{current_tokens} tokens")
            return optimized_messages
        
        return parsed_messages
        
    except Exception as e:
        log.error(f"❌ Error obteniendo historial optimizado: {e}")
        return []


async def clear_history(chat_id: str):
    """
    Limpia la memoria temporal de un chat.
    """
    await redis_client.delete(f"chat:{chat_id}:history")
