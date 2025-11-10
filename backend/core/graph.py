# app/core/graph.py

from fastapi.responses import StreamingResponse
from services.retrieval import retrieve_context
from services.embeddings import get_embeddings
from services.indexing import upsert_chunks
from services.inference import call_llm, call_llm_stream
from services.conversation import get_recent_history, store_message, get_or_create_session
from services.db import get_db
from services.sql_agent import sql_agent
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Optional
from fastapi import Depends
import logging, json
import os


log = logging.getLogger(__name__)

template_dir = os.path.join(os.path.dirname(__file__), "../prompts")
#log.info(f"Prompt Templates Path: {template_dir}")

env = Environment(loader=FileSystemLoader(template_dir))

async def detect_intention(question: str) -> dict:  # ← Ahora retorna dict
    """Detección inteligente de intenciones usando el LLM"""

    try:
        prompt = render_prompt("detec_intention.j2", question=question)
        raw_response = await call_llm(prompt)
        
        # PARSEAR el JSON de la respuesta
        intention_data = parse_intention_response(raw_response)
        
        log.info(f"🎯 Intención detectada: {intention_data.get('category', 'unknown')}")
        return intention_data
        
    except Exception as e:
        log.error(f"❌ Error en detección de intención: {e}")
        return get_fallback_intention(question)

def parse_intention_response(raw_response: str) -> dict:
    """Convierte la respuesta del LLM en un diccionario válido"""
    
    if not raw_response:
        raise ValueError("Respuesta vacía del modelo")
    
    # Limpiar la respuesta
    cleaned = raw_response.strip()
    
    # Extraer JSON de bloques de código si existe
    if "```json" in cleaned:
        start = cleaned.find("```json") + 7
        end = cleaned.find("```", start)
        if end != -1:
            cleaned = cleaned[start:end].strip()
    elif "```" in cleaned:
        start = cleaned.find("```") + 3
        end = cleaned.find("```", start)
        if end != -1:
            cleaned = cleaned[start:end].strip()
    
    # Buscar el primer { y último }
    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}') + 1
    
    if start_idx == -1 or end_idx == -1:
        raise ValueError("No se encontró JSON en la respuesta")
    
    json_str = cleaned[start_idx:end_idx]
    
    # Parsear JSON
    intention_data = json.loads(json_str)
    
    # Validar estructura mínima
    if not isinstance(intention_data, dict):
        raise ValueError("La respuesta no es un objeto JSON válido")
    
    return intention_data

def get_fallback_intention(question: str) -> dict:
    """Intención de fallback cuando el modelo falla"""
    question_lower = question.lower().strip()
    
    # Lógica de fallback simple
    if not question or len(question.split()) <= 2:
        return {
            "category": "conversational",
            "subcategory": "greeting", 
            "reasoning": "Fallback: mensaje muy corto",
            "confidence": 0.6,
            "requires_sql_agent": False
        }
    
    if any(word in question_lower for word in ["hola", "buenos días", "hi", "hello"]):
        return {
            "category": "conversational",
            "subcategory": "greeting",
            "reasoning": "Fallback: saludo detectado", 
            "confidence": 0.8,
            "requires_sql_agent": False
        }
    
    # Default: información general
    return {
        "category": "information_retrieval",
        "subcategory": "factual",
        "reasoning": "Fallback: consulta genérica",
        "confidence": 0.5,
        "requires_sql_agent": False
    }

def render_prompt(template_name: str, **kwargs) -> str:
    template = env.get_template(template_name)
    return template.render(**kwargs)


async def handle_sql_query(question: str, user_id: str) -> str:
    """Maneja consultas SQL - versión simplificada"""
    
    try:
        log.info("🛠️ Procesando consulta con Agente SQL...")
        sql_result = await sql_agent.generate_sql(question)
        
        log.info(f"📊 Resultado completo del Agente SQL: {sql_result}")

        if sql_result.get("error"):
            return f"❌ Error en consulta SQL: {sql_result['error']}"
        
        # El Agente SQL ya ejecutó la consulta y tiene los resultados
        result_data = sql_result.get("result", {})
        rows = result_data.get("rows", [])
        columns = result_data.get("columns", [])
        
        # Formatear respuesta con toda la información disponible
        return format_sql_response_complete(question, sql_result)
        
    except Exception as e:
        log.error(f"❌ Error en flujo SQL: {e}")
        return f"❌ Error procesando tu consulta de datos: {str(e)}"
    
def format_sql_response_complete(question: str, sql_result: Dict) -> str:
    """Formatea respuesta usando TODA la información del Agente SQL"""
    
    # Extraer componentes de la respuesta
    sql_query = sql_result.get("sql", "")
    flow = sql_result.get("flow", "")
    reformulation = sql_result.get("reformulation", "")
    narrative = sql_result.get("narrative", "")
    result_data = sql_result.get("result", {})
    rows = result_data.get("rows", [])
    columns = result_data.get("columns", [])
    
    # Construir respuesta estructurada
    response_parts = []
    
    # 1. Confirmación de la consulta
    if reformulation:
        response_parts.append(f"🔍 **Consulta:** {reformulation}")
    else:
        response_parts.append(f"🔍 **Consulta:** {question}")
    
    # 2. Resultados de datos
    if not rows:
        response_parts.append("📊 **Resultado:** No se encontraron datos para tu consulta.")
    else:
        response_parts.append("📊 **Resultados encontrados:**")
        
        # Formatear los datos
        if len(rows) == 1 and len(columns) == 1:
            # Resultado simple: un valor
            value = rows[0][0] if rows[0] else "No disponible"
            response_parts.append(f"• **{columns[0]}**: {value}")
        elif len(rows) == 1:
            # Una fila con múltiples columnas
            for i, col in enumerate(columns):
                value = rows[0][i] if i < len(rows[0]) else "N/A"
                response_parts.append(f"• **{col}**: {value}")
        else:
            # Múltiples filas
            response_parts.append(f"• **Total de registros:** {len(rows)}")
            # Mostrar primeras filas como ejemplo
            for i, row in enumerate(rows[:3]):
                row_str = " | ".join([f"{val}" for val in row])
                response_parts.append(f"  {i+1}. {row_str}")
            if len(rows) > 3:
                response_parts.append(f"  ... y {len(rows) - 3} registros más")
    
    # 3. Explicación del proceso (si está disponible)
    if flow and "Flujo Técnico" in flow:
        # Extraer solo la parte explicativa sin el markdown
        flow_clean = flow.replace("##### 🔀 Flujo Técnico:\n", "").strip()
        if flow_clean:
            response_parts.append("\n⚙️ **Proceso:**")
            response_parts.append(flow_clean)
    
    # 4. Narrative adicional (si está disponible)
    if narrative:
        response_parts.append(f"\n💡 **Contexto:** {narrative}")

    response_sql = "\n".join(response_parts)
    log.info(f"Respuesta General SQL: {response_sql}")

    return "\n".join(response_parts)


async def route_based_on_intention(intention_data: dict, question: str, user_id: str):
    """Determina template y contexto basado en la intención"""
    
    category = intention_data.get("category")
    requires_sql = intention_data.get("requires_sql_agent", False)
    
    if requires_sql:
        return "sql_bypass.j2", []

    if category == "conversational":
        return "chat_smalltalk.j2", []
    
    elif category == "text_improvement":
        return "rephrase.j2", []
    
    elif category == "content_creation":
        return "content_creation.j2", []
    
    elif category == "document_analysis":
        # Solo buscar contexto si la pregunta menciona documentos específicos
        context_chunks = await retrieve_context(question, user_id=user_id)
        return "rag_chat.j2", context_chunks
    
    else:  # information_retrieval, data_query, technical_support
        # Buscar en base de conocimiento
        context_chunks = await retrieve_context(question, user_id=user_id)
        return "rag_chat.j2", context_chunks

async def build_chat_pipeline(question: str, user_id: str, username: str = None, chat_id: str = None, db = None):
    """
    Construye el pipeline completo de chat y retorna todos los componentes necesarios.
    """
    
    # 1️⃣ Detección de intención
    intention_data = await detect_intention(question)
    log.info(f"🧭 Intención: {intention_data['category']} -> {intention_data['subcategory']}")
    
    # 2️⃣ Routing basado en intención
    template, context_chunks = await route_based_on_intention(intention_data, question, user_id)
    
    # 3️⃣ 🚨 SI ES SQL: Ejecutar inmediatamente y obtener respuesta
    sql_response = None
    if intention_data.get("requires_sql_agent"):
        log.info("🔍 Ejecutando SQL Agent para inyección en template")
        sql_response = await handle_sql_query(question, user_id)
    
    # 4️⃣ Generar título
    title_prompt = render_prompt("titles_prompt.j2", message=question, user_name=username, intention=intention_data["category"])
    title_chat = await call_llm(title_prompt)
    
    # 5️⃣ Crear sesión (si se proporciona db)
    session = None
    if db:
        session = await get_or_create_session(db, user_id, chat_id, title_chat)
        await store_message(db, session.id, user_id, "user", question)
    
    # 6️⃣ Construir prompt final (inyectando sql_response si existe)
    memory_context = await get_recent_history(session.id)
    
    log.info(f"Memory Context: {memory_context}")
    prompt = render_prompt(
        template,
        question=question,
        context=context_chunks,
        memory=memory_context,
        user_name=username,
        intention=intention_data["category"],
        subcategory=intention_data["subcategory"],
        sql_response=sql_response
    )
    
    return {
        "prompt": prompt,
        "session": session,
        "intention_data": intention_data,
        "context_chunks": context_chunks,
        "memory_context": memory_context,
        "title_chat": title_chat,
        "sql_response": sql_response  # 🚨 Para referencia
    }

async def run_rag_chat(question: str, user_id: str, db, chat_id: str = None, username: str = None):
    """Versión normal (sin streaming)"""
    
    # Usar pipeline común
    pipeline_data = await build_chat_pipeline(question, user_id, username, chat_id, db)
    
    # Inferencia normal
    answer = await call_llm(pipeline_data["prompt"])
    
    # Guardar respuesta
    if pipeline_data["session"]:
        await store_message(db, pipeline_data["session"].id, user_id, "assistant", answer)
    
    return {
        "chat_id": pipeline_data["session"].id if pipeline_data["session"] else None,
        "intention": pipeline_data["intention_data"],
        "answer": answer,
        "context_used": len(pipeline_data["context_chunks"])
    }

async def run_rag_chat_stream(question: str, user_id: str, db, chat_id: str = None, username: str = None):
    """Versión streaming - misma lógica, diferente ejecución"""
    
    try:
        # Usar el MISMO pipeline común
        pipeline_data = await build_chat_pipeline(question, user_id, username, chat_id, db)
        
        # Enviar metadata inicial
        initial_data = {
            "chat_id": str(pipeline_data["session"].id) if pipeline_data["session"] else None,
            "intention": pipeline_data["intention_data"],
            "context_used": len(pipeline_data["context_chunks"]),
            "memory_used": len(pipeline_data["memory_context"]),
            "content": ""
        }
        yield f"data: {json.dumps(initial_data)}\n\n"
        
        # Streaming de la respuesta
        full_response = ""
        async for chunk in call_llm_stream(pipeline_data["prompt"]):
            if chunk:
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # Guardar respuesta completa
        if pipeline_data["session"]:
            await store_message(db, pipeline_data["session"].id, user_id, "assistant", full_response)
            
    except Exception as e:
        log.error(f"❌ Error en streaming: {e}")
        error_data = {"error": f"Error en streaming: {str(e)}"}
        yield f"data: {json.dumps(error_data)}\n\n"

async def run_rephrase(text: str, style: str = "") -> str:
    prompt = render_prompt(
        "rephrase.j2",
        text=text,
        style=style,
    )

    answer = await call_llm(prompt)
    return answer
