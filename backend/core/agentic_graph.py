# backend/core/agentic_graph.py

from typing import Dict, List, Optional, Any
import asyncio, json, logging, time
from fastapi.responses import StreamingResponse
from services.inference import call_llm
from services.retrieval import retrieve_context
from services.conversation import get_recent_history, store_message, get_or_create_session
from services.db import get_db

log = logging.getLogger("core.agentic_graph")

# Catálogo de herramientas disponibles en AltheIA
TOOLS = {
    "vector_search_company": "Políticas/procesos internos de la empresa",
    "vector_search_user_docs": "Documentos del usuario (PDF/archivos)",
    "query_business_api": "Datos vivos: tickets, pedidos, estados",
    "web_search": "Noticias/precios/eventos recientes",
    "direct_response": "Responder sin herramientas"
}

# --- Prompts del planificador y del generador ---

PLANNER_SYSTEM = """Eres un planificador de acciones paso a paso.
Dispones de herramientas y debes decidir en cada paso si:
- Ejecutas UNA herramienta con una breve instrucción de entrada, o
- Finalizas con la respuesta final.

Responde SIEMPRE en JSON estricto con este esquema:
{"action": "tool"|"final", "tool": "<nombre_o_vacio>", "input": "<breve_input_o_vacio>", "rationale": "<breve_motivo>"}

Reglas:
- Puedes llamar a múltiples herramientas EN SECUENCIA si aporta valor.
- Evita repetir una herramienta si su resultado no añade información nueva.
- Finaliza ("final") sólo cuando el contexto sea suficiente para responder.
Herramientas disponibles:
- vector_search_company
- vector_search_user_docs
- query_business_api
- web_search
- direct_response
"""

GENERATOR_SYSTEM = """Eres un asistente profesional. Integra toda la evidencia obtenida.
Si usaste herramientas, indica brevemente el origen (p.ej. 'políticas internas', 'documentos del usuario', 'API', 'web').
Si falta información, explica límites y el siguiente mejor paso."""

# --- Ejecución real de herramientas (adapta aquí integraciones) ---

async def _execute_tool(tool: str, question: str, tool_input: str, user_id: str, db) -> Dict[str, Any]:
    q = tool_input.strip() if tool_input else question

    if tool in ("vector_search_company", "vector_search_user_docs"):
        docs = retrieve_context(q, user_id=user_id, limit=6)
        text = "\n\n".join(f"- {d.get('text','')}" for d in docs) if docs else ""
        return {"tool": tool, "query": q, "hits": len(docs), "content": text}

    if tool == "query_business_api":
        # TODO: enlazar con tu servicio real
        return {"tool": tool, "query": q, "hits": 0, "content": "API empresarial aún no integrada."}

    if tool == "web_search":
        # TODO: enlazar con tu buscador on-prem
        return {"tool": tool, "query": q, "hits": 0, "content": "Web search aún no integrado."}

    if tool == "direct_response":
        return {"tool": tool, "query": q, "hits": 1, "content": ""}

    return {"tool": tool, "query": q, "hits": 0, "content": ""}

# --- Planificador (elige siguiente acción) ---

def _safe_json_loads(txt: str) -> Dict[str, Any]:
    try:
        return json.loads(txt)
    except Exception:
        # fallback minimalista: forzar "final" si el modelo no obedeció
        return {"action": "final", "tool": "", "input": "", "rationale": "parser_fallback"}

async def _plan_next_step(question: str, history: str, scratchpad: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    scratchpad: lista de pasos previos [{"tool":..., "query":..., "hits":..., "summary":...}]
    """
    user_block = {
        "role": "user",
        "content": (
            f"Pregunta: {question}\n\n"
            f"Historial reciente:\n{history}\n\n"
            f"Pasos previos (resumen):\n" +
            "\n".join([f"- {p.get('tool')}: hits={p.get('hits')} query='{p.get('query')}'"
                       for p in scratchpad]) +
            "\n\nDecide el próximo paso."
        )
    }
    msgs = [{"role": "system", "content": PLANNER_SYSTEM}, user_block]
    plan_raw = await call_llm(json.dumps(msgs, ensure_ascii=False))
    plan = _safe_json_loads(plan_raw)
    # Normaliza
    action = plan.get("action", "final").lower()
    tool = plan.get("tool", "").strip()
    tool = tool if tool in TOOLS else ("direct_response" if action == "final" else tool)
    return {"action": action, "tool": tool, "input": plan.get("input", ""), "rationale": plan.get("rationale", "")}

# --- Generación final ---

async def _generate_final(question: str, aggregated_ctx: List[Dict[str, Any]], reasoning_note: str) -> str:
    evidence = []
    for c in aggregated_ctx:
        if not c.get("content"): 
            continue
        tag = {
            "vector_search_company": "políticas internas",
            "vector_search_user_docs": "documentos del usuario",
            "query_business_api": "API empresarial",
            "web_search": "fuentes web",
            "direct_response": "conocimiento general"
        }.get(c["tool"], c["tool"])
        snippet = c["content"][:2000]
        evidence.append(f"[{tag}] {snippet}")
    ev_text = "\n\n".join(evidence) if evidence else ""

    msgs = [
        {"role": "system", "content": GENERATOR_SYSTEM},
        {"role": "user", "content": (
            f"PREGUNTA: {question}\n\n"
            f"CONTEXTO AGREGADO:\n{ev_text}\n\n"
            f"NOTA_DE_PLANIFICACIÓN: {reasoning_note[:800]}\n\n"
            f"RESPUESTA FINAL:"
        )}
    ]
    return await call_llm(json.dumps(msgs, ensure_ascii=False))

# --- Loop principal de chat con múltiples herramientas ---

async def run_agent_chat(
    question: str,
    user_id: str,
    db,
    chat_id: Optional[str] = None,
    username: Optional[str] = None,
    max_steps: int = 4,
    min_useful_hits: int = 1
) -> Dict[str, Any]:

    session = await get_or_create_session(db, user_id, chat_id, question)
    chat_id = session["session_id"]

    history_msgs = await get_recent_history(db, chat_id, limit=6)
    history = "\n".join(f"{m['role']}: {m['content']}" for m in history_msgs)

    scratchpad: List[Dict[str, Any]] = []
    used_tools: set = set()
    reasoning_trail: List[str] = []
    aggregated_ctx: List[Dict[str, Any]] = []

    for step in range(1, max_steps + 1):
        plan = await _plan_next_step(question, history, scratchpad)
        reasoning_trail.append(f"step{step}:{plan.get('rationale','')}")
        action = plan["action"]

        if action == "final":
            break

        tool = plan["tool"]
        # Evita bucles tontos: si ya usamos la misma tool sin nuevos hits, fuerza finalizar
        if tool in used_tools and step > 1 and scratchpad and scratchpad[-1].get("hits", 0) < min_useful_hits:
            break

        result = await _execute_tool(tool, question, plan["input"], user_id, db)
        used_tools.add(tool)
        aggregated_ctx.append(result)

        # Pequeño resumen para el planner
        summary = (result["content"][:280] if result.get("content") else "").replace("\n", " ")
        scratchpad.append({"tool": tool, "query": result["query"], "hits": result.get("hits", 0), "summary": summary})

        # Si no aporta nada, damos chance a otra tool; si aporta bien, el planner decidirá finalizar.

    final_answer = await _generate_final(question, aggregated_ctx, " | ".join(reasoning_trail))

    await store_message(db, chat_id, role="user", content=question)
    await store_message(db, chat_id, role="assistant", content=final_answer)

    return {
        "chat_id": chat_id,
        "tools_used": list(used_tools),
        "steps": len(scratchpad),
        "context_stats": [{"tool": c["tool"], "hits": c.get("hits", 0)} for c in aggregated_ctx],
        "answer": final_answer
    }

async def run_agent_chat_stream(*args, **kwargs):
    res = await run_agent_chat(*args, **kwargs)
    async def _gen():
        yield f"data: {json.dumps({'chunk': res['answer']})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(_gen(), media_type="text/event-stream")
