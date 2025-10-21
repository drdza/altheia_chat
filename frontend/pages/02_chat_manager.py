# frontend/pages/02_chat_manager.py
import streamlit as st
from services.auth_service import require_auth
from shared import utils
from components import chat_manager

# Configurar la página
st.set_page_config(
    page_title="Mis Conversaciones - AltheIA",
    page_icon="🗂️",
    layout="wide"
)

@require_auth
def main():
    # Cargar estilos
    utils.load_css("frontend/assets/styles.css")
    utils.apply_dynamic_background(True)
    
    # Sidebar simplificado
    with st.sidebar:
        st.logo("frontend/assets/img/altheia-logo-black.png", size="large")
        render_manager_navigation()

    # Contenido principal
    render_manager_interface()

def render_manager_navigation():
    """Navegación para gestión"""
    fullname = st.session_state.user_id.get("username")
    username = utils.get_simple_username(fullname, "first_only")
    
    st.markdown(
        f"""
        <div class="welcome-box">
            <div class="welcome-box user">💬 Administra tus chats, {username}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()
    
    if st.button("↩️ Volver al Chat", use_container_width=True, type="primary"):
        st.switch_page("pages/01_chat.py")
    
    st.markdown("---")

def render_manager_interface():
    """Interfaz de gestión"""
    st.title("💬 Mis conversaciones")
    st.markdown("Administra y organiza tus chats con AltheIA")
    
    st.markdown("---")
    
    # Componente de gestión
    chat_manager.chat_management_panel()

if __name__ == "__main__":
    main() 