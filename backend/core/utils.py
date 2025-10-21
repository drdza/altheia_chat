# backend/core/utils.py

import os
import tempfile
import uuid
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from services.loader import load_file
from services.indexing import chunk_text

log = logging.getLogger(__name__)

async def read_chunk_file(file: UploadFile, user_id: str, chat_id: str = None, is_public: bool = False) -> Dict[str, Any]:
    """
    Procesar archivo y preparar chunks con metadata enriquecida
    """
    # Generar un doc_id único
    doc_uuid = str(uuid.uuid4())
    current_time = datetime.utcnow().isoformat()

    log.info(f"Processing file: {file.filename}, size: {file.size}, user: {user_id}")
    
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, file.filename)

    try:
        # Leer contenido del archivo y calcular hash
        file_content = await file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Guardar archivo temporal
        with open(tmp_path, "wb") as f:
            f.write(file_content)

        # Procesar texto
        text = load_file(tmp_path)
        parts = chunk_text(text)

        # Metadata enriquecida
        base_metadata = {
            "doc_version": 1,
            "original_filename": file.filename,
            "upload_timestamp": current_time,
            "last_updated": current_time,
            "uploaded_by": user_id,
            "document_status": "active",  # Para filtros en retrieval
            "file_size": file.size,
            "file_hash": file_hash,
            "source": "file",
            "chunk_count": len(parts),
            "chat_id": chat_id,  # Vincular al chat si existe
            "content_type": file.content_type,
        }

        chunks = [{
            "doc_id": doc_uuid,
            "chunk_id": f"{doc_uuid}-{i}",
            "text": chunk,
            "metadata": {
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(parts),
            },
            "user_id": "PUBLIC" if is_public else user_id
        } for i, chunk in enumerate(parts)]            

        log.info(f"Prepared {len(chunks)} chunks for user {user_id}")

        return {
            "doc_id": doc_uuid,
            "chunks": chunks,
            "chunks_count": len(chunks),
            "file_hash": file_hash,
            "file_metadata": base_metadata  # Para registro en PostgreSQL
        }

    except Exception as e:
        log.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)