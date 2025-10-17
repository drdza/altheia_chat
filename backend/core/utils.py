
from ast import Dict
import tempfile, os, uuid, logging
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
from services.loader import load_file
from services.indexing import chunk_text

log = logging.getLogger(__name__)

async def read_chunk_file(file: UploadFile, user_id: str) -> Dict[str, Any]:
    
    # Generar un doc_id único
    doc_uuid = str(uuid.uuid4())

    log.info(f"Processing file: {file.filename}, size: {file.size}, user: {user_id}")
    
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, file.filename)

    try:

        with open(tmp_path, "wb") as f:
            f.write(await file.read())

        text = load_file(tmp_path)
        parts = chunk_text(text)

        chunks = [{
            "doc_id": doc_uuid,
            "chunk_id": f"{doc_uuid}-{i}",
            "text": chunk,
            "metadata": {"source": "file", "filename": file.filename, "i": i},
            "user_id": user_id
        } for i, chunk in enumerate(parts)]            

        log.info(f"Prepared {len(chunks)} chunks for user {user_id}")

        return {
            "doc_id": doc_uuid,
            "chunks": chunks,
            "chunks_count": len(chunks)
        }

    except Exception as e:
        log.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)