# frontend/auth_service.py

import requests
import streamlit as st
from shared.config import settings

BACKEND_URL = settings.ALTHEIA_BACKEND
API_KEY = settings.API_KEY


def login_user(username: str, password: str) -> str | None:
    """Autentica al usuario y guarda cookie JWT en la sesión persistente."""    
    try:
        r = st.session_state.session.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": username, "password": password},
            headers={"X-Api-Key": API_KEY},
            timeout=50,
        )
        if r.status_code == 200:
            u = get_current_user()            
            return u
        else:
            st.markdown('<div class="stAlertError">Credenciales inválidas</div>', unsafe_allow_html=True)
            return None
    except Exception as e:
        st.markdown(f'<div class="stAlertError">f"Error de conexión al backend: {e}"</div>', unsafe_allow_html=True)        
        return None

def get_current_user() -> str | None:
    """Obtiene el usuario actual llamando a /auth/me."""
    try:
        session = st.session_state.session
        r = session.get(f"{BACKEND_URL}/auth/me")
        if r.status_code == 200:
            return r.json().get("user")
        else:
            return None
    except Exception as e:
        st.error(f"Error verificando sesión: {e}")
        return None
        
def logout_user():
    """Cierra sesión y limpia cookies."""
    try:
        st.session_state.session.post(f"{BACKEND_URL}/auth/logout")        
        st.session_state.user_id = None
        st.session_state.chat_history = []
        st.session_state.chat_id = None
    except Exception as e:
        st.error(f"Error cerrando sesión: {e}")

def is_admin(user_id: str) -> bool:
    return user_id.get("user").lower() == "drodriguez"
