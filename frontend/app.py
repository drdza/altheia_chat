# frontend/app.py
import streamlit as st
import requests
from shared import utils

# --- Configuración inicial ---
st.set_page_config(
    page_title="AltheIA", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Estado inicial global ---
def initialize_session_state():
    default_keys = {
        "access_token": None,
        "user_id": None,
        "session": requests.Session(),
        "chat_id": None,
        "chat_history": [],
        "new_chat_mode": False,
    }
    for k, v in default_keys.items():
        if k not in st.session_state:
            st.session_state[k] = v

def main():
    initialize_session_state()
    
    # Cargar estilos
    utils.load_css("frontend/assets/styles.css")
    utils.apply_dynamic_background(bool(st.session_state.user_id))
    
    # Routing simple
    if st.session_state.user_id:
        st.switch_page("pages/01_chat.py")
    else:
        st.switch_page("pages/00_welcome.py")

if __name__ == "__main__":
    main()