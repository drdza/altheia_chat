# frontend/services/api.py

from fastapi import HTTPException
import requests, uuid, json
import streamlit as st
from typing import List, Dict
from shared.config import settings

BACKEND_URL = settings.ALTHEIA_BACKEND
API_KEY = settings.API_KEY

def _session():
    """Obtiene o crea la sesión HTTP persistente con cookies JWT."""
    if "session" not in st.session_state:
        st.session_state.session = requests.Session()
    return st.session_state.session    

def _headers(include_api_key=True):
    """Encabezados base; Authorization ya no es necesario con cookies JWT."""
    if include_api_key:
        return {"X-Api-Key": API_KEY}
    return {}    

def chat_with_bot(question: str, chat_id: str) -> str:
    session = _session()
    r = session.post(f"{BACKEND_URL}/chat/", json={"question": question, "chat_id": chat_id}, headers=_headers())
    r.raise_for_status()    
    response = r.json()    
    return {"answer": response["answer"], "chat_id": response["chat_id"]}

def chat_with_bot_stream(question: str, chat_id: str = None):
    """Chat con streaming - nueva función"""
    session = _session()  

    payload = {
        "question": question,
        "chat_id": chat_id if chat_id is not None else ""
    }

    try:
        response = session.post(
            f"{BACKEND_URL}/chat/stream",
            json=payload,
            headers=_headers(),
            stream=True,
            timeout=30
        )
        response.raise_for_status()        
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])                        
                        yield data
                    except json.JSONDecodeError:                        
                        continue
                        
    except Exception as e:
        yield {"error": f"Error de conexión: {str(e)}"}


def rephrase_text(text: str, style: str) -> str:
    session = _session()
    r = session.post(f"{BACKEND_URL}/chat/rephrase", json={"text": text, "style": style}, headers=_headers())
    r.raise_for_status()
    return r.json()["rephrased"]

def upload_user_file(file:str) -> bool:
    session = _session()
    files = {"file": (file.name, file)}
    data = {"doc_id": uuid.uuid4()}
    r = session.post(f"{BACKEND_URL}/chat/ingest-file", files=files, data=data, headers=_headers())
    return r.status_code == 200

def upload_public_file(file: str) -> bool:
    session = _session()
    files = {"file": (file.name, file)}
    data = {"doc_id": uuid.uuid4()}
    r = session.post(f"{BACKEND_URL}/admin/ingest-file", files=files, data=data, headers=_headers())
    return r.status_code == 200

def reset_vectorstore() -> bool:
    session = _session()   
    r = session.post(f"{BACKEND_URL}/admin/recreate-collection", headers=_headers())
    return r.json()


def get_user_chats() -> List[Dict]:
    session = _session()
    r = session.get(f"{BACKEND_URL}/chat/sessions", headers=_headers())
    r.raise_for_status()
    return r.json()

def get_chat_history(session_id: str) -> List[Dict]:
    session = _session()
    r = session.get(f"{BACKEND_URL}/chat/history/{session_id}", headers=_headers())
    r.raise_for_status()
    return r.json()    