import streamlit as st
from services import api

def get_user_chats():
    with st.sidebar.expander("💭 Mis Chats", expanded=False):
        # --- Obtener chats ---
        chats = api.get_user_chats()
        if not chats:
            st.info("No hay chats anteriores")
            return
            
        col1, col2 = st.columns(2, vertical_alignment='center')        
    
        with col1:
            if st.button("✨ Nuevo", use_container_width=True, type="primary", help="Nuevo Chat"):
                st.session_state.chat_history = []
                st.session_state.chat_id = None
                st.session_state.new_chat_mode = True
                st.rerun()
    
        with col2:
            if st.button("🗂️ Admin.", use_container_width=True, help="Administrar conversaciones"):
                st.switch_page("pages/02_chat_manager.py")
                

        chat_options = {f"{chat['title']}": chat['session_id'] for chat in chats}

        # --- Control de modo "nuevo chat" ---
        if st.session_state.get("new_chat_mode", False):
            selectbox_key = f"chat_selectbox_reset_{st.session_state.get('reset_counter', 0)}"
            st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1
            st.session_state.new_chat_mode = False
        else:
            selectbox_key = "chat_selectbox_stable"
        
        # --- Selectbox persistente ---
        selected_title = st.selectbox(
            "Seleccione un chat:",
            options=list(chat_options.keys()),
            index=None,
            key=selectbox_key,
            label_visibility="collapsed",
            placeholder="Chats anteriores"
        )

        # --- Cargar chat seleccionado ---
        if selected_title:
            chat_id = chat_options[selected_title]
            if st.session_state.get("chat_id") != chat_id:
                st.session_state.chat_id = chat_id
                chats_data = api.get_chat_history(chat_id)
                st.session_state.chat_history = chats_data["history"]

# Función para mostrar el panel de gestión (se llamará desde app.py)
def show_chat_management_modal():
    """Muestra el modal de gestión de chats si está activado"""
    if st.session_state.get('show_chat_management', False):
        # Overlay modal
        st.markdown(
            """
            <style>
            .management-modal {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                z-index: 1000;
                width: 90%;
                max-width: 800px;
                max-height: 80vh;
                overflow-y: auto;
            }
            .modal-backdrop {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 999;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Backdrop
        st.markdown('<div class="modal-backdrop"></div>', unsafe_allow_html=True)
        
        # Modal content
        with st.container():
            st.markdown('<div class="management-modal">', unsafe_allow_html=True)
            
            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h2 style="margin: 0; color: #A5A2EC;">🗂️ Gestión de Mis Chats</h2>
                    <div style="font-size: 1.5em;">📊</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            from components.chat_manager import chat_management_panel
            chat_management_panel()
            
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🚪 Cerrar Gestión", use_container_width=True, type="secondary"):
                    st.session_state.show_chat_management = False
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)