# frontend/pages/01_Chat_Principal.py

import streamlit as st
from services.auth_service import require_auth
from shared import utils
from components.chat_ui import chat_interface_stream

# Configurar la página
st.set_page_config(
    page_title="Chat con AltheIA",
    page_icon="💬",
    layout="centered"
)

# Configurar navegación personalizada
utils.setup_custom_navigation()

@require_auth
def main():
    # Cargar estilos
    utils.load_css("frontend/assets/styles.css")
    utils.apply_dynamic_background(True)
    
    # Sidebar con navegación
    with st.sidebar:
        st.logo("frontend/assets/img/altheia-logo-black.png", size="large")
        
        # Información de usuario
        if st.session_state.user_id:
            fullname = st.session_state.user_id.get("username")
            username = utils.get_simple_username(fullname)
            st.markdown(
                f"""
                <div style="background: rgba(165, 162, 236, 0.1); padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <div style="font-weight: 600; color: #A5A2EC;">👋 Hola, {username}</div>
                    <div style="font-size: 0.8em; color: #666;">Conectado al chat</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Navegación personalizada
        utils.render_custom_navigation("Chat Principal")
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            from services.auth_service import logout_user
            logout_user()
            st.rerun()
    
    # Header del chat
    st.markdown(
        """
        <div class='stTitleChat'><h1>
            Althe<span style='color: #A5A2EC;'>IA</span> Chat
        </h1></div>
        """,
        unsafe_allow_html=True
    )
    
    # Breadcrumb de navegación
    st.markdown(
        """
        <div style="background: rgba(165, 162, 236, 0.1); padding: 10px 15px; border-radius: 8px; margin: 10px 0; font-size: 0.9em;">
            🧭 <strong>Navegación:</strong> Inicio → <strong>Chat Principal</strong>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.divider()
    
    # Interfaz de chat
    chat_interface_stream()

if __name__ == "__main__":
    main()