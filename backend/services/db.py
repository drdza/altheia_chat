# backend/services/db.py
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from core.config import settings

DATABASE_URL = settings.DATABASE_ADMIN_URL
Base = declarative_base()

def _default_chat_title():
    # se calcula al insertar, no al importar el módulo
    # si prefieres puro server-side, quita el default y genera el título en app code
    return f"Chat {datetime.now(timezone.utc).isoformat().replace('+00:00','Z')}"

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, index=True)
    title = Column(String, default=_default_chat_title)  # 👈 default callable, no f-string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 👈
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    chunks_count = Column(Integer, default=0)
    doc_metadata = Column(JSON)

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    version = Column(Integer)
    file_hash = Column(String(64))
    doc_id = Column(String)  # id en Milvus
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    chunks_count = Column(Integer)

class UploadTransaction(Base):
    __tablename__ = "upload_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(String, index=True)
    user_id = Column(String)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
