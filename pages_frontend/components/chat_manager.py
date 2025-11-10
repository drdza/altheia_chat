# frontend/components/chat_manager.py

import streamlit as st
from datetime import datetime
from streamlit.elements.lib.layout_utils import WidthWithoutContent
from services import api

def chat_management_panel():
    """
    Componente para que los usuarios gestionen sus chats
    - Ver estadísticas de uso
    - Archivar/eliminar chats  
    - Cambiar títulos
    - Ver límites de uso
    """
    
    st.markdown("#### 📈 Mis estadísticas ")
    
    # Obtener chats del usuario
    chats = api.get_user_chats()        

    if not chats:
        st.info("No tienes chats guardados")
        return
    
    # Estadísticas
    total_chats = len(chats)
    max_chats = 20  # Esto podría venir de la API o configuración
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Chats Activos", f"{total_chats}/{max_chats}")
    
    with col2:
        st.metric("Disponibles", max_chats - total_chats)
    
    with col3:
        usage_percent = (total_chats / max_chats) * 100
        st.metric("Uso", f"{usage_percent:.1f}%")
    
    # Barra de progreso
    st.progress(usage_percent / 100)
    
    st.markdown("---")            
    
    st.markdown("#### 🗃️ Organizar mis chats ")
    
    with st.expander("**💬 Mis Chats**"):
        colChat1, colChat2 = st.columns(2)
        totalChats = len(chats)

        # Calcular el punto de división
        mid_point = (totalChats + 1) // 2
        chats_col1 = chats[:mid_point]
        chats_col2 = chats[mid_point:]

        with colChat1:
            for i, chat in enumerate(chats_col1):
                render_chat_card(chat, f"col1_{i}")

        with colChat2:
            for i, chat in enumerate(chats_col2):
                render_chat_card(chat, f"col2_{i}")    

def render_chat_card(chat, column_suffix):
    """Renderiza una tarjeta de chat individual"""
    with st.expander(f"💬 {chat['title']}", expanded=False):
        
        col_tit_1, col_tit_2 = st.columns([6,2])
        
        with col_tit_1:
            # Editar título
            new_title = st.text_input(
                "Título del chat:",
                value=chat['title'],
                key=f"title_{chat['session_id']}_{column_suffix}"
            )

        with col_tit_2:
            created_at = chat['created_at']
            date_object = datetime.fromisoformat(created_at)
            date_to_show = date_object.strftime("%d/%m/%Y")
            st.text_input("Creado el:",value=date_to_show, disabled=True)
        
        col1, col2, col3, col4 = st.columns([3, 3, 3, 2])
        
        with col1:
            disableBtn = False if new_title != chat['title'] else True
            if st.button("💾 Guardar", key=f"save_{chat['session_id']}_{column_suffix}", disabled=disableBtn):
                st.toast(f"🔔 **Título actualizado:** {new_title}", duration=5)
        
        with col2:
            if st.button("🗄️ Archivar", key=f"archive_{chat['session_id']}_{column_suffix}"):
                st.toast(f"🗄️ **Chat Archivado:** {chat['title']}", duration=5)                
        
        with col3:
            if st.button("🗑️ Eliminar", key=f"delete_{chat['session_id']}_{column_suffix}"):
                st.toast(f"🗑️ **Chat Eliminado:** {chat['title']}", duration=5)                     


def admin_chat_management():
    """
    Versión administrativa con más funcionalidades
    """
    st.header("👑 Administración de Chats")
    
    # Filtros para admin
    col1, col2 = st.columns(2)
    
    with col1:
        user_filter = st.text_input("Filtrar por usuario ID:")
    
    with col2:
        date_filter = st.date_input("Filtrar por fecha:")
    
    # Aquí iría la lógica específica para admin
    st.info("Panel administrativo - Funciones extendidas próximamente")