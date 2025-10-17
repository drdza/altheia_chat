# app/services/retrieval.py

import logging
from typing import List, Dict, Any
from pymilvus import connections, Collection
from sympy.geometry import entity
from core.config import settings
from services.embeddings import get_embeddings

log = logging.getLogger(__name__)

def _connect():
    connections.connect("default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)

def _get_collection() -> Collection:
    _connect()
    return Collection(settings.MILVUS_COLLECTION)

async def retrieve_context(query: str, user_id: str):
    collection = _get_collection()
    collection.load()
    
    log.info(f"Retrieval from milvus schema '{collection.name}' with user '{user_id}'")
    
    # Fase 1: Búsqueda semántica sin filtros
    vectors = await get_embeddings([query], input_type="query")  # << aquí
    search_params = {"metric_type": settings.MILVUS_METRIC, "params": {"nprobe": 16}}    
    log.info(f"Vectors: {len(vectors)}")
    
    # Buscar más resultados de los necesarios para tener margen
    limit = settings.MILVUS_TOP_K
    initial_results = collection.search(
        data=vectors,
        anns_field="embedding",
        param=search_params,
        limit=limit*3,
        output_fields=["doc_id", "chunk_id", "text", "user_id", "metadata"]
    )
    log.info(f"Inital results: {len(initial_results)}")
        
    # Fase 2: Filtrar por acceso
    filtered_docs = []
    for hits in initial_results:
        for hit in hits:
            
            doc_user_id = hit.entity.get('user_id')            

            # Verificar permisos
            if doc_user_id == "PUBLIC" or (user_id and doc_user_id == user_id):
                filtered_docs.append({
                    'doc_id': hit.entity.get('doc_id'),
                    'chunk_id': hit.entity.get('chunk_id'),
                    'text': hit.entity.get('text'),
                    'user_id': doc_user_id,
                    'score': hit.score,
                    'metadata': hit.entity.get('metadata', {})
                })

    # Ordenar por score y limitar
    filtered_docs.sort(key=lambda x: x['score'], reverse=True)
    final_results = filtered_docs[:limit]    
    
    collection.release()

    log.info(f"Final results: {len(final_results)}")
    return final_results