# app/services/indexing.py

import logging, uuid
from typing import Iterable, List, Dict, Any
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from core.config import settings
from services.embeddings import get_embeddings

log = logging.getLogger(__name__)

def _connect():
    connections.connect("default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)

def ensure_collection():
    _connect()
    name = settings.MILVUS_COLLECTION

    # Si la colección existe, la retorna
    if utility.has_collection(name):
        log.info(f"Ensure Collection: {settings.MILVUS_COLLECTION} already exists.")
        return Collection(name)

    # Incia proceso de creación de la colección
    fields = [
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),        
        FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDINGS_DIM),
    ]
    
    schema = CollectionSchema(fields=fields, description="AltheIA RAG collection")
    
    col = Collection(name=name, schema=schema)
    col.create_index(
        field_name="embedding",
        index_params={"index_type": settings.MILVUS_INDEX_TYPE,
                    "metric_type": settings.MILVUS_METRIC,
                    "params": {"nlist": 1024}}
    )

    col.load()
    log.info("Ensure Collection: Created successfully.")
    return col

def reset_collection_data():
    try:
        _connect()
        name = settings.MILVUS_COLLECTION

        if utility.has_collection(name):
            utility.drop_collection(name)
            
        log.info(f"Todos los documentos en {name} fueron eliminados correctamente")
        return {"success": True, "collection": name}

    except Exception as e:
        log.error(f"Error al resetear la colección {settings.MILVUS_COLLECTION}: {e}")
        return {"success": False, "collection": settings.MILVUS_COLLECTION, "error": str(e)}


def chunk_text(text: str, max_tokens: int = 150) -> List[str]:
    words = text.split()
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(current) >= max_tokens:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))                

    return chunks

async def upsert_chunks(chunks: List[Dict[str, Any]]):
    col = ensure_collection()

    texts = [c["text"] for c in chunks]      
    vectors = await get_embeddings(texts, input_type="passage")
    
    doc_ids = [c["doc_id"] for c in chunks]
    chunk_ids = [c["chunk_id"] for c in chunks]
    metadata = [c.get("metadata", {}) for c in chunks]
    user_ids = [c["user_id"] for c in chunks]

    entities = [doc_ids, chunk_ids, texts, metadata, user_ids, vectors]    
    
    col.insert(entities)
    col.flush()    
    
    return len(chunks)

async def delete_docs(doc_ids: List[str], user_id: str):
    col = ensure_collection()
    expr = f"user_id == '{user_id}' and doc_id in {tuple(doc_ids)}"
    res = col.delete(expr)
    col.flush()
    log.info(f"Deleted docs: {doc_ids}, result={res}")

