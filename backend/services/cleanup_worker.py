# backend/services/cleanup_worker.py

import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from services.db import UploadTransaction, get_db
from services.indexing import delete_docs

log = logging.getLogger(__name__)

async def cleanup_orphaned_chunks():
    """
    Limpieza periódica de chunks huérfanos (transacciones pendientes antiguas)
    """
    log.info("🔄 Iniciando limpieza de chunks huérfanos...")
    
    async for db in get_db():
        try:
            # Encontrar transacciones pendientes con más de 1 hora
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            result = await db.execute(
                select(UploadTransaction)
                .where(and_(
                    UploadTransaction.status == 'pending',
                    UploadTransaction.created_at < cutoff_time
                ))
            )
            stale_transactions = result.scalars().all()
            
            for tx in stale_transactions:
                log.warning(f"🧹 Limpiando transacción huérfana: {tx.id} para doc {tx.doc_id}")
                
                # Eliminar chunks de Milvus
                try:
                    await delete_docs([tx.doc_id], "SYSTEM")
                    log.info(f"✅ Chunks eliminados para doc {tx.doc_id}")
                except Exception as e:
                    log.error(f"⚠️ Error eliminando chunks para doc {tx.doc_id}: {e}")
                
                # Marcar transacción como limpiada
                tx.status = 'cleaned'
                tx.updated_at = datetime.utcnow()
            
            await db.commit()
            
            log.info(f"✅ Limpieza completada: {len(stale_transactions)} transacciones huérfanas procesadas")
            
        except Exception as e:
            log.error(f"❌ Error en cleanup_orphaned_chunks: {e}")
            await db.rollback()

# Para ejecutar periódicamente (ejemplo con asyncio)
async def start_cleanup_scheduler():
    """
    Programar limpieza periódica cada 6 horas
    """
    while True:
        await asyncio.sleep(6 * 60 * 60)  # 6 horas
        await cleanup_orphaned_chunks()