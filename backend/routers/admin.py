# app/routers/admin.py
import tempfile
import os, uuid, logging
from fastapi import APIRouter, Depends, Header, UploadFile, File, Form, HTTPException
from typing import Optional
from services.auth_jwt import get_current_user
from core.config import settings
from core.errors import Unauthorized
from services.loader import load_file
from core.utils import read_chunk_file
from services.indexing import ensure_collection, reset_collection_data, chunk_text, upsert_chunks, delete_docs
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

        await upsert_chunks(chunks, user_id='PUBLIC')
        return {"doc_id": doc_uuid, "chunks": len(chunks)}

    except:
        return {"doc_id": "", "chunks": 0}
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/ingest-file", response_model=FileIngestResponse)
async def admin_ingest_file(file: UploadFile = File(...), _: bool = Depends(require_api_key)):
    user_id = "PUBLIC"
    try:        
        result = await read_chunk_file(file, user_id)

        await upsert_chunks(result["chunks"])

        log.info(f"Upserted {result['chunks_count']} chunks for {user_id}")
        
        return {"doc_id": result["doc_id"], "chunks": result["chunks_count"]}

    except HTTPException:
        raise
    
    except Exception as e:
        log.error(f"Unexpected error in user_ingest_file: {e}")
        return {"doc_id": "", "chunks": 0}


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