from pymilvus import connections, Collection
from core.config import settings
from services.embeddings import get_embeddings


def test_vectorstore(top_k: int=5):
    connections.connect("default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
    col = Collection(settings.MILVUS_COLLECTION)
    col.load()

    print(f"--- EXPLORANDO: {col.name.upper()} ---\n")
    print(f"Esquema:\n {col.schema}\n")
    print(f"Total de entidades: {col.num_entities}")

    print(f"\n🔍 Consultando chunks visibles")
    results = col.query(        
        expr="doc_id != ''",
        output_fields=["doc_id", "chunk_id", "text", "metadata", "user_id"]
    )

    print(f"🔢 Chunks encontrados: {len(results)}\n")
    for i, doc in enumerate(results[:top_k]):
        print(f"--- Chunk {i+1} ---")
        print("📄 doc_id:", doc.get("doc_id"))
        print("🔢 chunk_id:", doc.get("chunk_id"))
        print("🧠 user_id:", doc.get("user_id"))
        print("📝 text:", doc.get("text")[:200], "...\n")

def insert_dummy_vector():
    from pymilvus import Collection, connections, utility
    import uuid

    connections.connect("default", host="altheia", port="19530")
    
    col_name = "altheia_docs"
    if not utility.has_collection(col_name):
        print("No existe la colección")
    else:
        col = Collection(col_name)
        print("✅ Esquema de la colección:")    
        print(col.schema)

        entity = [            
            ["doc_test"],                 # doc_id
            ["doc_test-0"],               # chunk_id
            ["texto de prueba"],          # text
            [{"source":"test"}],          # metadata
            ["PUBLIC"],                   # user_id
            [[0.1]*1024]                  # embedding
        ]
        print("Insertando 1 entidad...")
        col.insert(entity)
        col.flush()
        print("Insert OK")

async def two_phase_search(question, user_id=None, limit=10):
    """Búsqueda en dos fases: primero semántica, luego filtro de acceso"""
    
    connections.connect("default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
    collection = Collection(settings.MILVUS_COLLECTION)
    collection.load()
    
    # Fase 1: Búsqueda semántica sin filtros
    vectors = await get_embeddings([question], input_type="query") 
    
    search_params = {
        "metric_type": settings.MILVUS_METRIC,
        "params": {"nprobe": 10}
    }
    
    # Buscar más resultados de los necesarios para tener margen
    initial_results = collection.search(
        data=vectors,
        anns_field="doc_id",
        param=search_params,
        limit=limit * 3,  # Buscar más para filtrar después
        output_fields=["doc_id", "chunk_id", "text", "user_id", "metadata"]
    )
    print(f"Inital results: {len(initial_results)}")
    
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
    return final_results

if __name__ == "__main__":
    import asyncio
    question = input("Question: ")
    user = input("User: ")
    result = asyncio.run(two_phase_search(question, user))
    print(result)