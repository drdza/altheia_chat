# backend/services/transaction_manager.py

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from services.db import UploadTransaction, Document, DocumentVersion
from services.indexing import delete_docs

log = logging.getLogger(__name__)

class TransactionManager:
    
    async def begin_upload_transaction(self, db: AsyncSession, doc_id: str, user_id: str) -> str:
        """Iniciar transacción distribuida para upload"""
        transaction_id = str(uuid.uuid4())
        
        # Registrar intento en PostgreSQL
        transaction_record = UploadTransaction(
            id=transaction_id,
            doc_id=doc_id,
            user_id=user_id,
            status='pending',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(transaction_record)
        await db.commit()
        
        log.info(f"📝 Transacción iniciada: {transaction_id} para doc {doc_id}")
        return transaction_id
    
    async def commit_upload(self, db: AsyncSession, transaction_id: str, document_data: Dict):
        """Confirmar transacción exitosa - registrar documento en PostgreSQL"""
        try:
            # 1. Registrar documento principal
            document = Document(
                id=uuid.UUID(document_data["id"]),
                user_id=document_data["user_id"],
                chat_id=document_data["chat_id"],
                original_filename=document_data["original_filename"],
                file_hash=document_data["file_hash"],
                current_version=1,
                document_type=document_data.get("document_type", "user_private"),
                status="active",
                chunks_count=document_data["chunks_count"],
                metadata=document_data.get("metadata", {})
            )
            db.add(document)
            
            # 2. Registrar versión inicial
            version = DocumentVersion(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_data["id"]),
                version=1,
                file_hash=document_data["file_hash"],
                doc_id=document_data["id"],
                chunks_count=document_data["chunks_count"],
                created_at=datetime.now()
            )
            db.add(version)
            
            # 3. Marcar transacción como completada
            await db.execute(
                update(UploadTransaction)
                .where(UploadTransaction.id == transaction_id)
                .values(status='completed', updated_at=datetime.now())
            )
            
            await db.commit()
            log.info(f"✅ Transacción completada: {transaction_id}")
            
        except Exception as e:
            await db.rollback()
            log.error(f"❌ Error en commit_upload: {e}")
            raise
    
    async def rollback_upload(self, db: AsyncSession, transaction_id: str, doc_id: str):
        """Revertir transacción fallida - eliminar chunks de Milvus"""
        try:
            # 1. Eliminar chunks de Milvus si se insertaron
            log.info(f"🔄 Iniciando rollback para doc {doc_id}")
            await delete_docs([doc_id], "SYSTEM")
            
        except Exception as e:
            log.error(f"⚠️  Error en rollback Milvus: {e}")
        
        try:
            # 2. Marcar transacción como fallida
            await db.execute(
                update(UploadTransaction)
                .where(UploadTransaction.id == transaction_id)
                .values(status='failed', updated_at=datetime.now())
            )
            await db.commit()
            log.info(f"🗑️  Transacción marcada como fallida: {transaction_id}")
            
        except Exception as e:
            log.error(f"⚠️  Error marcando transacción como fallida: {e}")
    
    async def check_transaction_exists(self, db: AsyncSession, transaction_id: str) -> bool:
        """Verificar si una transacción ya fue procesada"""
        result = await db.execute(
            select(UploadTransaction)
            .where(UploadTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none() is not None

# Instancia global
transaction_manager = TransactionManager()