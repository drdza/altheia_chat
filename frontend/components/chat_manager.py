# frontend/components/chat_manager.py

import streamlit as st
from services import api

def chat_management_panel():
    """
    Componente para que los usuarios gestionen sus chats
    - Ver estadísticas de uso
    - Archivar/eliminar chats  
    - Cambiar títulos
    - Ver límites de uso
    """
    
    st.header("🗂️ Gestión de Mis Chats")
    
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
    
    # Lista de chats para gestionar
    st.subheader("Mis Chats")
    
    for chat in chats:
        with st.expander(f"💬 {chat['title']}", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Editar título
                new_title = st.text_input(
                    "Título del chat:",
                    value=chat['title'],
                    key=f"title_{chat['session_id']}"
                )
                if new_title != chat['title']:
                    if st.button("💾 Guardar", key=f"save_{chat['session_id']}"):
                        # Aquí iría la llamada a API para actualizar título
                        st.success(f"Título actualizado: {new_title}")
                        st.rerun()
            
            with col2:
                if st.button("📁 Archivar", key=f"archive_{chat['session_id']}"):
                    st.warning("Función de archivado próximamente")
            
            with col3:
                if st.button("🗑️ Eliminar", key=f"delete_{chat['session_id']}"):
                    st.error("Función de eliminación próximamente")

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