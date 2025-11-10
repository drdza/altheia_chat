# backend/services/conversation.py

import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.db import ChatSession, ChatMessage
from services.memory import redis_client, save_message, get_history
import logging

log = logging.getLogger("services.conversation")

# ======================================================
# 🧩 Función: Crear o recuperar una sesión existente
# ======================================================
async def get_or_create_session(db: AsyncSession, user_id: str, chat_id: Optional[str] = None, title: str = None) -> ChatSession:
    """
    Devuelve una sesión existente o crea una nueva.
    Si no se pasa chat_id, crea un nuevo hilo.
    """
    if chat_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
        session = result.scalar_one_or_none()
        if session:
            return session

    # Si no existe, creamos una nueva
    new_session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    log.info(f"🆕 Nueva sesión creada: {new_session.id} para {user_id}")
    return new_session

# ======================================================
# 💬 Función: Guardar mensaje (usuario o asistente)
# ======================================================
async def store_message(db: AsyncSession, chat_id: str, user_id: str, role: str, content: str):
    """
    Guarda un mensaje tanto en PostgreSQL como en Redis.
    """
    message = ChatMessage(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        role=role,
        content=content,
        timestamp=datetime.now()
    )
    db.add(message)
    await db.commit()

    # Memoria corta: Redis
    await save_message(chat_id, role, content)

    log.info(f"💾 Mensaje guardado: chat={chat_id} role={role}")
    return message

# ======================================================
# 🧩 Función: Obtener historial completo de un chat
# ======================================================
async def get_full_history(db: AsyncSession, chat_id: str) -> List[Dict]:
    """
    Recupera todo el historial persistente (desde PostgreSQL).
    """
    log.info(f"Chat ID: {chat_id}")

    result = await db.execute(
        select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(ChatMessage.timestamp.asc())
    )
    messages = result.scalars().all()
    
    log.info(f"{len(messages)} recovered messages")

    return [
        {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
        for m in messages
    ]

# ===================================================================
# 🧩 Función: Obtener las sesiones de un usuario (chats anteriores)
# ===================================================================
async def get_user_sessions(db: AsyncSession, user_id:str ) -> List[Dict]:
    """
    Devuelve las sesiones (chats) anteriores del usuario.
    """
    log.info(f"Session User: {user_id}")

    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
    )

    sessions = result.scalars().all()  
    
    return [
        {
            "session_id": str(session.id),
            "title": session.title or f"Chat {session.created_at.strftime('%Y-%m-%d %H:%M')}",
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        for session in sessions
    ]

# ======================================================
# ⚡ Función: Obtener contexto inmediato (desde Redis)
# ======================================================
async def get_recent_history(chat_id: str) -> List[Dict]:
    """
    Recupera los últimos mensajes recientes desde Redis.
    """
    try:
        return await get_history(chat_id)
    except Exception as e:
        log.error(f"❌ Error recuperando historial Redis: {e}")
        return []

# ======================================================
# 🧹 Función: Borrar un chat (solo en PostgreSQL)
# ======================================================
async def delete_session(db: AsyncSession, chat_id: str):
    """
    Elimina un hilo completo (solo para administradores o limpieza).
    """
    await db.execute(ChatMessage.__table__.delete().where(ChatMessage.chat_id == chat_id))
    await db.execute(ChatSession.__table__.delete().where(ChatSession.id == chat_id))
    await db.commit()
    log.warning(f"🗑️ Sesión eliminada: {chat_id}")
