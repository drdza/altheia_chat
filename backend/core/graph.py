# app/core/graph.py

from fastapi.responses import StreamingResponse
from services.retrieval import retrieve_context
from services.embeddings import get_embeddings
from services.indexing import upsert_chunks
from services.inference import call_llm, call_llm_stream
from services.conversation import get_recent_history, store_message, get_or_create_session
from services.db import get_db
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
    """
    Clasifica la intención del usuario con reglas simples.
    Retorna: 'rephrase', 'analyze_user_doc', 'rag_chat', 'small_talk'
    """
    q = question.lower().strip()

    if any(w in q for w in ["reformula", "reescribe", "mejorar redacción", "rephrase"]):
        return "rephrase"
    if any(w in q for w in ["analiza", "documento", "archivo", "pdf", "word", "excel"]):
        return "analyze_user_doc"
    if len(q.split()) < 4:
        return "small_talk"
    return "rag_chat"

def render_prompt(template_name: str, **kwargs) -> str:
    template = env.get_template(template_name)
    return template.render(**kwargs)

async def run_rag_chat(
    question: str,
    user_id: str,
    db=Depends(get_db),
    chat_id: Optional[str] = None,
    username: Optional[str] = None
):
    """
    Pipeline completo de conversación con memoria, intención y RAG.
    """

    # 1️⃣ Detectar intención
    intent = await detect_intention(question)
    log.info(f"🧭 Intención detectada: {intent}")

    # 2️⃣ Generar titulo de la sesión
    title_chat = ""
    template = "titles_prompt.j2"
    prompt = render_prompt(
        template,
        message=question,
        user_name=username,
        intention=intent,        
    )
    title_chat = await call_llm(prompt)
    
    log.info(f"Chat ID: {chat_id}")
    # 3️⃣ Crear o recuperar sesión
    session = await get_or_create_session(db, user_id, chat_id, title_chat)

    # 4️⃣ Guardar mensaje del usuario
    await store_message(db, session.id, user_id, "user", question)

    # 5️⃣ Obtener memoria reciente (Redis)
    memory_context = ""
    # memory_context = await get_recent_history(session.id)

    # 6️⃣ Recuperar contexto relevante según intención
    if intent == "rephrase":
        template = "rephrase.j2"
        context_chunks = []
    elif intent == "analyze_user_doc":
        context_chunks = await retrieve_context(question, user_id=user_id)
        template = "rag_chat.j2"
    elif intent == "small_talk":
        context_chunks = []
        template = "chat_smalltalk.j2"
    else:  # RAG normal
        context_chunks = await retrieve_context(question, user_id=user_id)
        template = "rag_chat.j2"

    # 7️⃣ Construir prompt dinámico
    prompt = render_prompt(
        template,
        question=question,
        context=context_chunks,
        memory=memory_context,
        user_name=username,
    )

    # 8️⃣ Inferencia
    answer = await call_llm(prompt)

    # 9️⃣ Guardar respuesta
    await store_message(db, session.id, user_id, "assistant", answer)

    # log.info(f"💬 Respuesta generada para {user_id}: {answer[:100]}...")

    return {
        "chat_id": session.id,
        "intent": intent,
        "answer": answer,
        "context_used": len(context_chunks),
        "memory_used": len(memory_context),
    }


async def run_rag_chat_stream(
    question: str,
    user_id: str,
    db,
    chat_id: Optional[str] = None,
    username: Optional[str] = None
):
    """
    Versión con streaming del pipeline de chat
    """
    try:
        # 1️⃣-6️⃣ Misma lógica que run_rag_chat (hasta construir el prompt)
        intent = await detect_intention(question)
        log.info(f"🧭 Intención detectada: {intent}")
        
        # Generar título
        title_chat = ""
        template = "titles_prompt.j2"
        prompt_title = render_prompt(
            template,
            message=question,
            user_name=username,
            intention=intent,        
        )
        title_chat = await call_llm(prompt_title)
        
        # Crear sesión
        session = await get_or_create_session(db, user_id, chat_id, title_chat)
        
        # Guardar mensaje del usuario
        await store_message(db, session.id, user_id, "user", question)
        
        # Obtener contexto
        memory_context = ""
        # memory_context = await get_recent_history(session.id)
        if intent == "rephrase":
            template = "rephrase.j2"
            context_chunks = []
        elif intent == "analyze_user_doc":
            context_chunks = await retrieve_context(question, user_id=user_id)
            template = "rag_chat.j2"
        elif intent == "small_talk":
            context_chunks = []
            template = "chat_smalltalk.j2"
        else:
            context_chunks = await retrieve_context(question, user_id=user_id)
            template = "rag_chat.j2"
        
        # Construir prompt final
        prompt = render_prompt(
            template,
            question=question,
            context=context_chunks,
            memory=memory_context,
            user_name=username,
        )
        
        # Devolver metadata inicial
        initial_data = {
            "chat_id": str(session.id),
            "intent": intent,
            "context_used": len(context_chunks),
            "memory_used": len(memory_context),
            "content": ""
        }
        yield f"data: {json.dumps(initial_data)}\n\n"        

        # 7️⃣ Streaming de la respuesta
        full_response = ""
        async for chunk in call_llm_stream(prompt):
            if chunk:
                full_response += chunk
                # Enviar chunk al cliente
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # 8️⃣ Guardar respuesta completa al final
        await store_message(db, session.id, user_id, "assistant", full_response)

    except Exception as e:
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
