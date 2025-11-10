# backend/services/db.py

import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from core.config import settings

DATABASE_URL = settings.DATABASE_ADMIN_URL

Base = declarative_base()

# 🧩 Tablas existentes
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, index=True)
    title = Column(String, default=f"Chat {datetime.now(timezone.utc)}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # <- Cambiado
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc)) 

# 🆕 NUEVAS TABLAS para gestión documental
class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    original_filename = Column(String)
    file_hash = Column(String(64))
    current_version = Column(Integer, default=1)
    document_type = Column(String(20), default='user_private')
    status = Column(String(20), default='active')
    chunks_count = Column(Integer, default=0)  
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # <- Cambiado
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # <- Cambiado
    doc_metadata = Column(JSON)

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    version = Column(Integer)
    file_hash = Column(String(64))
    doc_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # <- Cambiado
    chunks_count = Column(Integer)

class UploadTransaction(Base):
    __tablename__ = "upload_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(String, index=True)
    user_id = Column(String)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # <- Cambiado
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # <- Cambiado

# 🧠 Conexión
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# 🛠️ Inicialización automática
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
