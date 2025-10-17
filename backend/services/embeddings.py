import logging, httpx
from typing import List
from core.config import settings

log = logging.getLogger(__name__)

def _auth_headers():
    # No agregues Authorization si está vacío o con espacios
    if settings.EMBEDDINGS_API_KEY and settings.EMBEDDINGS_API_KEY.strip():
        return {"Authorization": f"Bearer {settings.EMBEDDINGS_API_KEY.strip()}"}
    return {}

async def embed_remote(texts: List[str], *, input_type: str) -> List[List[float]]:
    assert settings.EMBEDDINGS_API_URL, "EMBEDDINGS_API_URL no configurado"

    # NVIDIA NIM-style payload (nv-embedqa-e5-v5)
    is_nvidia = str(settings.EMBEDDINGS_MODEL).startswith("nvidia/")
    payload = {
        "input": texts if len(texts) > 1 else texts[0],
        "model": settings.EMBEDDINGS_MODEL,
    }
    if is_nvidia:
        payload.update({
            "input_type": input_type,          # "query" para búsquedas, "passage" para documentos
            "encoding_format": "float",
            "truncate": "NONE",
            "user": "altheia",
        })

    headers = {"accept": "application/json", "Content-Type": "application/json"}
    headers.update(_auth_headers())    
    
    log.info(f"Embedding payload: num_inputs={len(texts)}, avg_len={sum(len(t) for t in texts)//len(texts)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(settings.EMBEDDINGS_API_URL, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    # NVIDIA/NIM suele devolver: {"data":[{"embedding":[...], "index":0}, ...]}
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        out = []
        for item in data["data"]:
            emb = item.get("embedding") or item.get("vector")  # por si cambian key
            if emb is None:
                continue
            out.append(emb)
        # Si input era string, devolver [[...]]
        if len(texts) == 1 and out and isinstance(out[0][0], (int, float)):
            return [out[0]]
        return out

    # OpenAI-like fallback: {"data":[{"embedding":[...]}]}
    if "embeddings" in data and isinstance(data["embeddings"], list):
        return data["embeddings"]

    # Último recurso: si ya es lista de listas
    if isinstance(data, list) and data and isinstance(data[0], list):
        return data
    raise RuntimeError(f"Formato de respuesta de embeddings no reconocido: {str(data)[:200]}")

async def get_embeddings(texts: List[str], *, input_type: str) -> List[List[float]]:
    if settings.EMBEDDINGS_API_URL:
        return await embed_remote(texts, input_type=input_type)

