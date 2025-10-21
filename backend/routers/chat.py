# app/routers/chat.py

import os, tempfile, logging, json
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse, FileIngestResponse, RephraseRequest, RephraseResponse
from core.graph import run_rag_chat, run_rag_chat_stream, run_rephrase
from services.auth_jwt import get_current_user
from core.utils import read_chunk_file
from services.indexing import upsert_chunks
from services.db import get_db
from services.conversation import get_or_create_session, get_full_history, get_user_sessions
from services.transaction_manager import transaction_manager

log = logging.getLogger(__name__)
router = APIRouter()

# ======================================================
# 💬 Endpoint principal del chat (memoria + RAG híbrido)
# ======================================================
@router.post("/", summary="Interacción principal del chat")
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user)
):
    """
    Endpoint principal del chat:
    - Crea sesión o reutiliza una existente.
    - Procesa la pregunta usando el pipeline híbrido.
    - Devuelve la respuesta, intención y trazabilidad.
    """
    # log.info(f"User Info: {user}")

    try:
        # 1️⃣ Ejecutar el pipeline híbrido con memoria y RAG
        result = await run_rag_chat(
            question=req.question,
            user_id=user["user"],
            db=db,
            chat_id=req.chat_id,
            username=user["username"],
        )

        return {
            "chat_id": result["chat_id"],
            "intent": result["intent"],
            "answer": result["answer"],
            "context_used": result["context_used"],
            "memory_used": result["memory_used"]
        }

    except Exception as e:
        log.exception(f"❌ Error en /chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando chat: {str(e)}")

@router.post("/stream", summary="Chat con streaming")
async def chat_stream(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user)
):
    """
    Endpoint de chat con respuesta en streaming
    """
    try:
        async def generate():
            async for chunk in run_rag_chat_stream(
                question=req.question,
                user_id=user["user"],
                db=db,
                chat_id=req.chat_id,
                username=user["username"],
            ):
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Importante para Nginx
            }
        )
        
    except Exception as e:
        log.exception(f"❌ Error en /chat/stream: {e}")
        async def error_stream():
            error_data = {"error": f"Error: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")



# ======================================================
# 🧾 Endpoint para recuperar historial completo
# ======================================================
@router.get("/history/{session_id}", summary="Recuperar historial de conversación")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Devuelve todos los mensajes almacenados para una sesión específica.
    """

    try:
        history = await get_full_history(db, session_id)
        return {"session_id": session_id, "history": history}

    except Exception as e:
        log.exception(f"❌ Error al recuperar historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# 💭 Endpoint para recuperar las sesiones del usuario
# ======================================================
@router.get("/sessions")
async def list_user_chats(db: AsyncSession = Depends(get_db), user: str = Depends(get_current_user)):
    user_id = user["user"]
    try:
        sessions = await get_user_sessions(db, user_id)
        return sessions

    except Exception as e:
        log.exception(f"❌ Error al recuperar las sesiones del usuario '{user_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))        


# ======================================================
# 🧩 Endpoint para iniciar un nuevo chat
# ======================================================
@router.post("/new", summary="Iniciar un nuevo chat")
async def new_chat(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Crea una nueva sesión de chat vacía.
    """
    session = await get_or_create_session(db, user_id)
    return {"chat_id": session.id, "title": session.title}


# ==================================================================
# 🤔 Endpoint para iniciar el servicio del refraseo o reformulación
# ==================================================================
@router.post("/rephrase", response_model=RephraseResponse)
async def rephrase(req: RephraseRequest):
    result = await run_rephrase(req.text, style=req.style or "")
    return {"rephrased": result}


# ==============================================================
# 📤 Endpoint para ingestar un documento nuevo a la vectorstore
# ==============================================================
@router.post("/ingest-file", response_model=FileIngestResponse)
async def user_ingest_file(
    file: UploadFile = File(...), 
    user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = user["user"]
    transaction_id = None
    
    try:        
        # 1. PREPARE: Procesar archivo y generar transaction
        result = await read_chunk_file(file, user_id)
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
            "metadata": result.get("file_metadata", {})
        }
        await transaction_manager.commit_upload(db, transaction_id, document_data)

        log.info(f"✅ Upload completado: {result['doc_id']} - {result['chunks_count']} chunks")
        
        return {
            "doc_id": result["doc_id"], 
            "chunks": result["chunks_count"],
            "message": "Document uploaded successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        log.error(f"❌ Error en user_ingest_file: {e}")
        
        # COMPENSACIÓN: Revertir cambios en caso de error
        if transaction_id and 'result' in locals():
            await transaction_manager.rollback_upload(db, transaction_id, result["doc_id"])
        
        return {
            "doc_id": "", 
            "chunks": 0, 
            "message": f"Error processing file: {str(e)}"
        }