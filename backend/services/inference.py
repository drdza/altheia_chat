# app/services/inference.py

import json
import httpx, logging
from fastapi.responses import StreamingResponse
from core.config import settings

from core.errors import BadGateway

log = logging.getLogger(__name__)

async def call_llm_stream(prompt: str):
    """Versión con streaming del LLM"""
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "stream": True  # ¡Importante para streaming!
    }
    
    headers = {}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
    headers["Accept"] = "text/event-stream"

    timeout = httpx.Timeout(settings.LLM_TIMEOUT, connect=5.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream(
                "POST", 
                str(settings.LLM_API_URL), 
                json=payload, 
                headers=headers
            ) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        # Procesar chunk según el formato de tu proveedor LLM
                        yield process_stream_chunk(chunk)
                        
        except httpx.HTTPError as e:
            log.exception("LLM upstream error")
            yield json.dumps({"error": str(e)})

def process_stream_chunk(chunk: str) -> str:
    """Procesa el chunk según el formato del proveedor LLM"""
    try:
        # Para OpenAI-compatible
        if chunk.startswith("data: "):
            if chunk.strip() == "data: [DONE]":
                return ""
            data = json.loads(chunk[6:])
            if "choices" in data and data["choices"]:
                delta = data["choices"][0].get("delta", {})
                return delta.get("content", "")
        
        # Para otros formatos, ajusta según tu proveedor
        return chunk
    except:
        return ""

async def call_llm(prompt: str) -> str:
    payload = {"messages": [{"role": "user", "content": prompt}]}
    headers = {}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    timeout = httpx.Timeout(settings.LLM_TIMEOUT, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(str(settings.LLM_API_URL), json=payload, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            log.exception("LLM upstream error")
            raise BadGateway(str(e)) from e

    data = resp.json()

    # Acepta varios esquemas de proveedores
    for key in ("answer", "content", "output", "text"):
        if key in data:
            return data[key]
            
    if isinstance(data, dict) and "choices" in data and data["choices"]:
        msg = data["choices"][0].get("message", {})
        return msg.get("content") or str(data)
    return str(data)
