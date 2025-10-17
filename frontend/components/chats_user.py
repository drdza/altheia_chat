import streamlit as st
from admin import admin_memory
from services import api


def get_user_chats():
     
    with st.sidebar.expander("💭 Mis Chats", expanded=True):
          # --- Obtener chats ---
        chats = api.get_user_chats()
        if not chats:
            return

        st.link_button("Admin. Chats", "admin_memory.py", use_container_width=True)

        col1, col2 = st.columns([2,6], vertical_alignment='center')

        with col1:
            # --- Botón Nuevo Chat ---
            if st.button("➕", use_container_width=True, type="primary", help="✨ Nuevo Chat"):
                st.session_state.chat_history = []
                st.session_state.chat_id = None
                st.session_state.new_chat_mode = True



        chat_options = {f"{chat['title']}": chat['session_id'] for chat in chats}

        # --- Control de modo "nuevo chat" ---
        # Creamos una key estable que solo cambia la PRIMER vez después del botón
        if st.session_state.get("new_chat_mode", False):
            selectbox_key = f"chat_selectbox_reset_{st.session_state.get('reset_counter', 0)}"
            st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1
            # desactivar inmediatamente para que no cambie la key otra vez
            st.session_state.new_chat_mode = False
        else:
            selectbox_key = "chat_selectbox_stable"

        with col2:
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

