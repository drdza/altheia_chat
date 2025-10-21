# frontend/pages/01_chat.py
import streamlit as st
from services.auth_service import require_auth
from shared import utils
from components.chat_ui import chat_interface_stream
from components import chats_user, user_tools

# Configurar la página
st.set_page_config(
    page_title="AltheIA Chat",
    page_icon="💬",
    layout="centered"
)

@require_auth
def main():
    # Cargar estilos
    utils.load_css("frontend/assets/styles.css")
    utils.apply_dynamic_background(True)
    
    # Sidebar simplificado
    with st.sidebar:
        st.logo("frontend/assets/img/altheia-logo-black.png", size="large")
        
        # Info usuario y logout
        render_user_info()
                
        # Chats del usuario
        chats_user.get_user_chats()
        user_tools.load_user_options()

    # Contenido principal del chat
    render_chat_interface()

def render_user_info():
    """Muestra info del usuario y botón logout"""
    fullname = st.session_state.user_id.get("username")
    username = utils.get_simple_username(fullname)
    
    st.markdown(
        f"""
        <div class="welcome-box">
            <div class="box-overlay user">👋 Hola, {username}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

def render_chat_navigation():
    """Navegación mínima para el chat"""


def render_chat_interface():
    """Interfaz principal del chat"""
    st.markdown(
        """
        <div class='stTitleChat'><h1>
            Althe<span style='color: #A5A2EC;'>IA</span> Chat
        </h1></div>
        """,
        unsafe_allow_html=True
    )
    
    st.divider()
    chat_interface_stream()

if __name__ == "__main__":
    main()