# app/routers/admin.py

import tempfile
import os, uuid, logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Header, UploadFile, File, Form, HTTPException
from typing import Optional
from services.auth_jwt import get_current_user
from core.config import settings
from core.errors import Unauthorized
from services.loader import load_file
from core.utils import read_chunk_file
from services.indexing import ensure_collection, reset_collection_data, chunk_text, upsert_chunks, delete_docs
from services.db import get_db
from services.transaction_manager import transaction_manager
from models.schemas import (
    IngestRequest, UpsertRequest, DeleteRequest,
    StatusResponse, ResetResponse,
    IngestResponse, UpsertResponse, DeleteResponse,
    GenericCountResponse, FileIngestResponse
)

log = logging.getLogger(__name__)

router = APIRouter()
ADMIN_USER = ["drodriguez", "ingdatos01.pab"]

def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    log.info(f"API Key received: {x_api_key}")
    if x_api_key != settings.API_KEY:
        raise Unauthorized("Invalid or missing API key")
    return True

@router.post("/recreate-collection", response_model=StatusResponse)
async def admin_recreate_collection(_: bool = Depends(require_api_key)):    
    try:
        result = reset_collection_data()
        if not result["success"]:
            return {
                "status": "error",
                "message": f"Error al borrar colección: {result['error']}"
            }
        col = ensure_collection()
        return {"status": "ok", "message": f"Colección '{col.name}' recreada correctamente"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/ingest-file-", response_model=FileIngestResponse)
async def _admin_ingest_file(file: UploadFile = File(...), _: bool = Depends(require_api_key)):

    log.info(f"Received file: {file.filename}, size: {file.size}")
    
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, file.filename)

    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    try:
        text = load_file(tmp_path)
        parts = chunk_text(text)
        doc_uuid = str(uuid.uuid4())

        chunks = [{
            "doc_id": f"{doc_uuid}",
            "chunk_id": f"{doc_uuid}-{i}",
            "text": chunk,
            "metadata": {"source": "file", "filename": file.filename, "i": i}
        } for i, chunk in enumerate(parts)]            

        log.info(f"Ready to upsert chunks: {len(chunks)}")

        await upsert_chunks(chunks)
        return {"doc_id": doc_uuid, "chunks": len(chunks)}

    except:
        return {"doc_id": "", "chunks": 0}
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/ingest-file", response_model=FileIngestResponse)
async def admin_ingest_file(
    file: UploadFile = File(...), 
    _: bool = Depends(require_api_key),
    db: AsyncSession = Depends(get_db)
):
    user_id = "PUBLIC"
    transaction_id = None
    
    try:        
        # 1. PREPARE: Procesar archivo y generar transaction
        result = await read_chunk_file(file, user_id, is_public=True)
        transaction_id = await transaction_manager.begin_upload_transaction(db, result["doc_id"], user_id)
        
        # 2. COMMIT FASE 1: Insertar en Milvus
        await upsert_chunks(result["chunks"], transaction_id)
        
        # 3. COMMIT FASE 2: Registrar en PostgreSQL
        document_data = {
            "id": result["doc_id"],
            "user_id": user_id,
            "original_filename": file.filename,
            "file_hash": result["file_hash"],
            "chunks_count": result["chunks_count"],
            "document_type": "public_base",  # ← Especificar que es documento público
            "metadata": result.get("file_metadata", {})
        }
        await transaction_manager.commit_upload(db, transaction_id, document_data)

        log.info(f"✅ Admin upload completado: {result['doc_id']} - {result['chunks_count']} chunks")
        
        return {
            "doc_id": result["doc_id"], 
            "chunks": result["chunks_count"],
            "message": "Public document uploaded successfully"
        }

    except HTTPException:
        raise
    
    except Exception as e:
        log.error(f"❌ Error en admin_ingest_file: {e}")
        
        # COMPENSACIÓN: Revertir cambios en caso de error
        if transaction_id and 'result' in locals():
            await transaction_manager.rollback_upload(db, transaction_id, result["doc_id"])
        
        return {
            "doc_id": "", 
            "chunks": 0, 
            "message": f"Error processing file: {str(e)}"
        }


@router.post("/delete", response_model=DeleteResponse)
async def admin_delete(req: DeleteRequest, user_id: str = Depends(get_current_user), _: bool = Depends(require_api_key)):
    await delete_docs(req.doc_ids, user_id)
    return {"deleted_doc_ids": req.doc_ids}


# @router.post("/ingest-raw", response_model=IngestResponse)
# async def admin_ingest_raw(doc_id: str, text: str, _: bool = Depends(require_api_key)):
#     parts = chunk_text(text)
#     chunks = [{
#         "chunk_id": f"{doc_id}-{i}",
#         "text": chunk,
#         "metadata": {"source": "raw", "i": i}
#     } for i, chunk in enumerate(parts)]
#     await upsert_chunks(chunks, user_id='PUBLIC')
#     return {"doc_id": doc_id, "chunks": len(chunks)}