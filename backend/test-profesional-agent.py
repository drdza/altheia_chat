# agentic_reasoning.py
# Agente con razonamiento, ruteo estructurado y tools tipadas (listo para producción ligera)

import asyncio, json, re, time, os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Protocol, Tuple
from contextlib import asynccontextmanager

import aiohttp

ALTHEIA_BASE_URL = os.getenv("ALTHEIA_BASE_URL", "http://altheia.gruporeyes.org:8001/v1")
CHAT_ENDPOINT = f"{ALTHEIA_BASE_URL}/chat/completions"
MODEL_ROUTER = os.getenv("ROUTER_MODEL", "llama-3.1-8b-instruct")       # chico y barato para rutear
MODEL_RESPONDER = os.getenv("RESP_MODEL", "llama-3.1-70b-instruct")     # grande para responder
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# ----------------------------- Infra: cliente HTTP con retries -----------------------------

@asynccontextmanager
async def _session():
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        yield s

async def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with _session() as s:
                async with s.post(url, json=payload) as r:
                    r.raise_for_status()
                    return await r.json()
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.8 * (2 ** attempt))
    raise RuntimeError(f"HTTP error after retries: {last_err}")

async def call_chat(model: str, messages: List[Dict[str, str]],
                    temperature: float = 0.2, max_tokens: int = 512) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    data = await _post_json(CHAT_ENDPOINT, payload)
    return data["choices"][0]["message"]["content"]

# ----------------------------- Contratos de Tools -----------------------------

class Tool(Protocol):
    name: str
    description: str
    async def run(self, query: str, **kwargs) -> Dict[str, Any]: ...

@dataclass
class ToolResult:
    ok: bool
    name: str
    data: Dict[str, Any]
    took_ms: int
    error: Optional[str] = None

@dataclass
class VectorSearchCompany:
    name: str = "vector_search_company"
    description: str = "Knowledge base corporativa"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        # TODO: integrar llamada real; aquí un mock tipado
        await asyncio.sleep(0.2)
        return {"hits": 5, "snippets": ["Política de vacaciones 2024 actualizada", "Procedimiento de tickets"], "query": query}

@dataclass
class VectorSearchUserDocs:
    name: str = "vector_search_user_docs"
    description: str = "Documentos subidos por el usuario"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        return {"hits": 3, "files": ["acuerdo.pdf", "manual.pdf"], "query": query}

@dataclass
class QueryBusinessAPI:
    name: str = "query_business_api"
    description: str = "APIs empresariales (tickets, pedidos, métricas)"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.15)
        return {"tickets_in_progress": 15, "resolved_week": 8, "query": query, "ts": time.time()}

@dataclass
class WebSearch:
    name: str = "web_search"
    description: str = "Búsqueda web reciente"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.25)
        return {"sources": ["fuente_confiable_1", "fuente_confiable_2"], "query": query}

@dataclass
class DirectResponse:
    name: str = "direct_response"
    description: str = "Respuesta directa sin herramientas"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        return {"note": "no_tool_needed", "query": query}

TOOLS: Dict[str, Tool] = {
    "vector_search_company": VectorSearchCompany(),
    "vector_search_user_docs": VectorSearchUserDocs(),
    "query_business_api": QueryBusinessAPI(),
    "web_search": WebSearch(),
    "direct_response": DirectResponse(),
}

# ----------------------------- Estado del agente -----------------------------

@dataclass
class AgentState:
    question: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    tool_decision: Optional[str] = None
    tool_output: Optional[ToolResult] = None
    reasoning: Optional[str] = None
    final_answer: Optional[str] = None

# ----------------------------- Router estructurado -----------------------------

ROUTER_SYSTEM = """Eres un router estricto. Devuelve un JSON con el siguiente esquema:
{"tool": "<one_of: vector_search_company | vector_search_user_docs | query_business_api | web_search | direct_response>",
 "confidence": 0..1,
 "reason": "<breve justificación>"}
No incluyas texto adicional ni explicaciones fuera del JSON.
"""

def _safe_json(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s.strip())
    except Exception:
        # Intenta extraer el primer bloque JSON si vino con ruido
        m = re.search(r'\{.*\}', s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

async def router_decide(question: str) -> Tuple[str, float, str]:
    user = f"Pregunta: {question}\nElige la tool que maximiza veracidad y frescura de la respuesta."
    out = await call_chat(MODEL_ROUTER, [{"role": "system", "content": ROUTER_SYSTEM},
                                         {"role": "user", "content": user}],
                         temperature=0.0, max_tokens=120)
    j = _safe_json(out) or {}
    tool = j.get("tool") if j.get("tool") in TOOLS else "direct_response"
    conf = float(j.get("confidence", 0.0))
    reason = j.get("reason", "")
    return tool, conf, reason

# ----------------------------- Razonamiento y generación -----------------------------

RESP_SYSTEM = """Eres un asistente profesional. Usa la evidencia proporcionada. 
Si usaste herramientas, menciona de manera breve la fuente (KB interna, docs del usuario, API, web).
Si la evidencia es insuficiente, dilo y sugiere el siguiente paso mínimo para obtenerla.
Sé conciso y claro.
"""

async def generate_reasoning_and_answer(state: AgentState) -> Tuple[str, str]:
    ctx_lines = []
    if state.tool_output and state.tool_output.ok:
        ctx_lines.append(f"[{state.tool_output.name}] {json.dumps(state.tool_output.data)[:700]}")
    elif state.tool_output and not state.tool_output.ok:
        ctx_lines.append(f"[{state.tool_output.name}] ERROR: {state.tool_output.error}")

    ctx = "\n".join(ctx_lines) if ctx_lines else "sin_evidencia"
    prompt_user = (
        f"PREGUNTA: {state.question}\n"
        f"HERRAMIENTA: {state.tool_decision}\n"
        f"EVIDENCIA:\n{ctx}\n\n"
        "Primero, redacta en una sola línea tu plan de respuesta entre <plan>...</plan>.\n"
        "Luego entrega la respuesta final clara para el usuario."
    )

    out = await call_chat(MODEL_RESPONDER,
                          [{"role": "system", "content": RESP_SYSTEM},
                           {"role": "user", "content": prompt_user}],
                          temperature=0.2, max_tokens=700)

    plan_match = re.search(r"<plan>(.*?)</plan>", out, flags=re.S)
    plan = plan_match.group(1).strip() if plan_match else "plan_no_detectado"
    return plan, out.replace(plan_match.group(0), "").strip() if plan_match else out.strip()

# ----------------------------- Orquestación -----------------------------

async def run_agent(question: str) -> Dict[str, Any]:
    t0 = time.time()
    state = AgentState(question=question)

    # 1) Router estructurado con fallback
    tool_name, confidence, reason = await router_decide(question)
    state.tool_decision = tool_name

    # 2) Ejecución de tool con timeouts y captura de error
    tool = TOOLS[tool_name]
    start = time.time()
    try:
        data = await asyncio.wait_for(tool.run(question), timeout=REQUEST_TIMEOUT)
        state.tool_output = ToolResult(ok=True, name=tool.name, data=data,
                                       took_ms=int((time.time()-start)*1000))
    except Exception as e:
        state.tool_output = ToolResult(ok=False, name=tool.name, data={}, took_ms=int((time.time()-start)*1000),
                                       error=str(e))

    # 3) Verificación de suficiencia mínima
    sufficient = False
    if state.tool_output.ok:
        if tool_name == "direct_response":
            sufficient = True
        elif tool_name in ("vector_search_company", "vector_search_user_docs"):
            sufficient = state.tool_output.data.get("hits", 0) > 0
        elif tool_name == "query_business_api":
            sufficient = "tickets_in_progress" in state.tool_output.data
        elif tool_name == "web_search":
            sufficient = len(state.tool_output.data.get("sources", [])) >= 1

    # Degradación: si no es suficiente, intenta una búsqueda web como segunda pasada
    if not sufficient and tool_name != "web_search":
        fallback_tool = TOOLS["web_search"]
        start2 = time.time()
        try:
            data2 = await asyncio.wait_for(fallback_tool.run(question), timeout=REQUEST_TIMEOUT)
            # agrega evidencia de fallback
            state.tool_output = ToolResult(ok=True, name=f"{tool.name}+web_search",
                                           data={"primary": state.tool_output.data, "fallback_web": data2},
                                           took_ms=int((time.time()-start2)*1000 + state.tool_output.took_ms))
            sufficient = True
            state.tool_decision = f"{tool_name}→web_search"
        except Exception as e:
            # mantenemos el resultado original pero anotamos el fallo
            state.tool_output.error = f"{state.tool_output.error or ''} | fallback_web_error: {e}"

    # 4) Razonamiento + respuesta final
    plan, answer = await generate_reasoning_and_answer(state)
    state.reasoning = plan
    state.final_answer = answer

    return {
        "success": True,
        "decision": {"tool": state.tool_decision, "router_confidence": confidence, "router_reason": reason},
        "tool": {"ok": state.tool_output.ok, "name": state.tool_output.name, "took_ms": state.tool_output.took_ms},
        "answer": state.final_answer,
        "elapsed_ms": int((time.time()-t0)*1000),
    }

# CLI simple para pruebas manuales
if __name__ == "__main__":
    while True:
        q = input("Pregunta: ").strip()
        if q == "exit":
            break
        print(asyncio.run(run_agent(q)))
# agentic_reasoning.py
# Agente con razonamiento, ruteo estructurado y tools tipadas (listo para producción ligera)

import asyncio, json, re, time, os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Protocol, Tuple
from contextlib import asynccontextmanager

import aiohttp

ALTHEIA_BASE_URL = os.getenv("ALTHEIA_BASE_URL", "http://altheia.gruporeyes.org:8001/v1")
CHAT_ENDPOINT = f"{ALTHEIA_BASE_URL}/chat/completions"
MODEL_ROUTER = os.getenv("ROUTER_MODEL", "llama-3.1-8b-instruct")       # chico y barato para rutear
MODEL_RESPONDER = os.getenv("RESP_MODEL", "llama-3.1-70b-instruct")     # grande para responder
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# ----------------------------- Infra: cliente HTTP con retries -----------------------------

@asynccontextmanager
async def _session():
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        yield s

async def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with _session() as s:
                async with s.post(url, json=payload) as r:
                    r.raise_for_status()
                    return await r.json()
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.8 * (2 ** attempt))
    raise RuntimeError(f"HTTP error after retries: {last_err}")

async def call_chat(model: str, messages: List[Dict[str, str]],
                    temperature: float = 0.2, max_tokens: int = 512) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    data = await _post_json(CHAT_ENDPOINT, payload)
    return data["choices"][0]["message"]["content"]

# ----------------------------- Contratos de Tools -----------------------------

class Tool(Protocol):
    name: str
    description: str
    async def run(self, query: str, **kwargs) -> Dict[str, Any]: ...

@dataclass
class ToolResult:
    ok: bool
    name: str
    data: Dict[str, Any]
    took_ms: int
    error: Optional[str] = None

@dataclass
class VectorSearchCompany:
    name: str = "vector_search_company"
    description: str = "Knowledge base corporativa"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        # TODO: integrar llamada real; aquí un mock tipado
        await asyncio.sleep(0.2)
        return {"hits": 5, "snippets": ["Política de vacaciones 2024 actualizada", "Procedimiento de tickets"], "query": query}

@dataclass
class VectorSearchUserDocs:
    name: str = "vector_search_user_docs"
    description: str = "Documentos subidos por el usuario"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        return {"hits": 3, "files": ["acuerdo.pdf", "manual.pdf"], "query": query}

@dataclass
class QueryBusinessAPI:
    name: str = "query_business_api"
    description: str = "APIs empresariales (tickets, pedidos, métricas)"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.15)
        return {"tickets_in_progress": 15, "resolved_week": 8, "query": query, "ts": time.time()}

@dataclass
class WebSearch:
    name: str = "web_search"
    description: str = "Búsqueda web reciente"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.25)
        return {"sources": ["fuente_confiable_1", "fuente_confiable_2"], "query": query}

@dataclass
class DirectResponse:
    name: str = "direct_response"
    description: str = "Respuesta directa sin herramientas"

    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        return {"note": "no_tool_needed", "query": query}

TOOLS: Dict[str, Tool] = {
    "vector_search_company": VectorSearchCompany(),
    "vector_search_user_docs": VectorSearchUserDocs(),
    "query_business_api": QueryBusinessAPI(),
    "web_search": WebSearch(),
    "direct_response": DirectResponse(),
}

# ----------------------------- Estado del agente -----------------------------

@dataclass
class AgentState:
    question: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    tool_decision: Optional[str] = None
    tool_output: Optional[ToolResult] = None
    reasoning: Optional[str] = None
    final_answer: Optional[str] = None

# ----------------------------- Router estructurado -----------------------------

ROUTER_SYSTEM = """Eres un router estricto. Devuelve un JSON con el siguiente esquema:
{"tool": "<one_of: vector_search_company | vector_search_user_docs | query_business_api | web_search | direct_response>",
 "confidence": 0..1,
 "reason": "<breve justificación>"}
No incluyas texto adicional ni explicaciones fuera del JSON.
"""

def _safe_json(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s.strip())
    except Exception:
        # Intenta extraer el primer bloque JSON si vino con ruido
        m = re.search(r'\{.*\}', s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

async def router_decide(question: str) -> Tuple[str, float, str]:
    user = f"Pregunta: {question}\nElige la tool que maximiza veracidad y frescura de la respuesta."
    out = await call_chat(MODEL_ROUTER, [{"role": "system", "content": ROUTER_SYSTEM},
                                         {"role": "user", "content": user}],
                         temperature=0.0, max_tokens=120)
    j = _safe_json(out) or {}
    tool = j.get("tool") if j.get("tool") in TOOLS else "direct_response"
    conf = float(j.get("confidence", 0.0))
    reason = j.get("reason", "")
    return tool, conf, reason

# ----------------------------- Razonamiento y generación -----------------------------

RESP_SYSTEM = """Eres un asistente profesional. Usa la evidencia proporcionada. 
Si usaste herramientas, menciona de manera breve la fuente (KB interna, docs del usuario, API, web).
Si la evidencia es insuficiente, dilo y sugiere el siguiente paso mínimo para obtenerla.
Sé conciso y claro.
"""

async def generate_reasoning_and_answer(state: AgentState) -> Tuple[str, str]:
    ctx_lines = []
    if state.tool_output and state.tool_output.ok:
        ctx_lines.append(f"[{state.tool_output.name}] {json.dumps(state.tool_output.data)[:700]}")
    elif state.tool_output and not state.tool_output.ok:
        ctx_lines.append(f"[{state.tool_output.name}] ERROR: {state.tool_output.error}")

    ctx = "\n".join(ctx_lines) if ctx_lines else "sin_evidencia"
    prompt_user = (
        f"PREGUNTA: {state.question}\n"
        f"HERRAMIENTA: {state.tool_decision}\n"
        f"EVIDENCIA:\n{ctx}\n\n"
        "Primero, redacta en una sola línea tu plan de respuesta entre <plan>...</plan>.\n"
        "Luego entrega la respuesta final clara para el usuario."
    )

    out = await call_chat(MODEL_RESPONDER,
                          [{"role": "system", "content": RESP_SYSTEM},
                           {"role": "user", "content": prompt_user}],
                          temperature=0.2, max_tokens=700)

    plan_match = re.search(r"<plan>(.*?)</plan>", out, flags=re.S)
    plan = plan_match.group(1).strip() if plan_match else "plan_no_detectado"
    return plan, out.replace(plan_match.group(0), "").strip() if plan_match else out.strip()

# ----------------------------- Orquestación -----------------------------

async def run_agent(question: str) -> Dict[str, Any]:
    t0 = time.time()
    state = AgentState(question=question)

    # 1) Router estructurado con fallback
    tool_name, confidence, reason = await router_decide(question)
    state.tool_decision = tool_name

    # 2) Ejecución de tool con timeouts y captura de error
    tool = TOOLS[tool_name]
    start = time.time()
    try:
        data = await asyncio.wait_for(tool.run(question), timeout=REQUEST_TIMEOUT)
        state.tool_output = ToolResult(ok=True, name=tool.name, data=data,
                                       took_ms=int((time.time()-start)*1000))
    except Exception as e:
        state.tool_output = ToolResult(ok=False, name=tool.name, data={}, took_ms=int((time.time()-start)*1000),
                                       error=str(e))

    # 3) Verificación de suficiencia mínima
    sufficient = False
    if state.tool_output.ok:
        if tool_name == "direct_response":
            sufficient = True
        elif tool_name in ("vector_search_company", "vector_search_user_docs"):
            sufficient = state.tool_output.data.get("hits", 0) > 0
        elif tool_name == "query_business_api":
            sufficient = "tickets_in_progress" in state.tool_output.data
        elif tool_name == "web_search":
            sufficient = len(state.tool_output.data.get("sources", [])) >= 1

    # Degradación: si no es suficiente, intenta una búsqueda web como segunda pasada
    if not sufficient and tool_name != "web_search":
        fallback_tool = TOOLS["web_search"]
        start2 = time.time()
        try:
            data2 = await asyncio.wait_for(fallback_tool.run(question), timeout=REQUEST_TIMEOUT)
            # agrega evidencia de fallback
            state.tool_output = ToolResult(ok=True, name=f"{tool.name}+web_search",
                                           data={"primary": state.tool_output.data, "fallback_web": data2},
                                           took_ms=int((time.time()-start2)*1000 + state.tool_output.took_ms))
            sufficient = True
            state.tool_decision = f"{tool_name}→web_search"
        except Exception as e:
            # mantenemos el resultado original pero anotamos el fallo
            state.tool_output.error = f"{state.tool_output.error or ''} | fallback_web_error: {e}"

    # 4) Razonamiento + respuesta final
    plan, answer = await generate_reasoning_and_answer(state)
    state.reasoning = plan
    state.final_answer = answer

    return {
        "success": True,
        "decision": {"tool": state.tool_decision, "router_confidence": confidence, "router_reason": reason},
        "tool": {"ok": state.tool_output.ok, "name": state.tool_output.name, "took_ms": state.tool_output.took_ms},
        "answer": state.final_answer,
        "elapsed_ms": int((time.time()-t0)*1000),
    }

# CLI simple para pruebas manuales
if __name__ == "__main__":
    q = input("Pregunta: ").strip()
    print(asyncio.run(run_agent(q)))
