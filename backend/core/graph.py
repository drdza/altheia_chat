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

async def detect_intention(question: str) -> str:
    """Detección inteligente de intenciones usando el LLM"""

    prompt = render_prompt(
        "detec_intention.j2",
        question=question,
    )
    intention = await call_llm(prompt)    
    return intention


def render_prompt(template_name: str, **kwargs) -> str:
    template = env.get_template(template_name)
    return template.render(**kwargs)

async def handle_sql_query(question: str, intention_data: Dict, user_id: str, pipeline_data: Dict) -> str:
    """Maneja todo el flujo de consultas SQL"""
    
    try:
        # 1. Generar SQL
        log.info("🛠️ Generando SQL desde lenguaje natural...")
        generate_result = await sql_agent.generate_sql(question)
        
        log.info(f"Resultados SQL: {generate_result}")

        if generate_result.get("error"):
            return f"❌ Error generando consulta: {generate_result['error']}"
        
        sql_query = generate_result.get("sql_query")
        if not sql_query:
            return "❌ No se pudo generar una consulta SQL válida para tu pregunta."
        
        log.info(f"📊 SQL generado: {sql_query}")
        
        # 2. Ejecutar SQL
        log.info("⚡ Ejecutando consulta SQL...")
        execute_result = await sql_agent.execute_sql(sql_query, user_id)
        
        if execute_result.get("error"):
            return f"❌ Error ejecutando consulta: {execute_result['error']}"
        
        data = execute_result.get("data", [])
        
        # 3. Formatear respuesta
        return ""
        
    except Exception as e:
        log.error(f"❌ Error en flujo SQL: {e}")
        return f"❌ Error procesando tu consulta de datos: {str(e)}"
    
    

async def route_based_on_intention(intention_data: dict, question: str, user_id: str):
    """Determina template y contexto basado en la intención"""
    
    category = intention_data.get("category")
    requires_sql = intention_data.get("requires_sql_agent", False)
    
    if requires_sql:
        return await handle_sql_agent_request(intention_data, question, user_id)

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
    Esta función centraliza la lógica común para evitar duplicación.
    """
    
    # 1️⃣ Detección de intención (NUEVO sistema)
    intention_data = await detect_intention(question)
    log.info(f"🧭 Intención: {intention_data['category']} -> {intention_data['subcategory']}")
    
    # 2️⃣ Routing basado en intención
    template, context_chunks = await route_based_on_intention(intention_data, question, user_id)
    
    # 3️⃣ Generar título
    title_prompt = render_prompt("titles_prompt.j2", message=question, user_name=username, intention=intention_data["category"])
    title_chat = await call_llm(title_prompt)
    
    # 4️⃣ Crear sesión (si se proporciona db)
    session = None
    if db:
        session = await get_or_create_session(db, user_id, chat_id, title_chat)
        await store_message(db, session.id, user_id, "user", question)
    
    # 5️⃣ Construir prompt final
    memory_context = await get_recent_history(session.id)
    prompt = render_prompt(
        template,
        question=question,
        context=context_chunks,
        memory=memory_context,
        user_name=username,
        intention=intention_data["category"],
        subcategory=intention_data["subcategory"],
    )
    
    return {
        "prompt": prompt,
        "session": session,
        "intention_data": intention_data,
        "context_chunks": context_chunks,
        "memory_context": memory_context,
        "title_chat": title_chat
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
