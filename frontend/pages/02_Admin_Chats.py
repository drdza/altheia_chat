# frontend/pages/02_Admin_Memorias.py

import streamlit as st
from services.auth_service import require_admin
from shared import utils
from components import chat_manager

# Configurar la página
st.set_page_config(
    page_title="Administración de Memorias - AltheIA",
    page_icon="🔧",
    layout="wide"
)

# Configurar navegación personalizada
utils.setup_custom_navigation()

@require_admin
def main():
    # Cargar estilos
    utils.load_css("frontend/assets/styles.css")
    utils.apply_dynamic_background(True)
    
    # Sidebar con navegación
    with st.sidebar:
        st.logo("frontend/assets/img/altheia-logo-black.png", size="large")
        
        # Información de usuario admin
        if st.session_state.user_id:
            fullname = st.session_state.user_id.get("username")
            username = utils.get_simple_username(fullname)
            st.markdown(
                f"""
                <div style="background: rgba(165, 162, 236, 0.1); padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <div style="font-weight: 600; color: #A5A2EC;">👑 {username}</div>
                    <div style="font-size: 0.8em; color: #666;">Modo Administrador</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Navegación personalizada
        utils.render_custom_navigation("Admin Memorias")
        
        # Herramientas rápidas admin
        st.markdown("---")
        st.subheader("⚡ Acciones Rápidas")
        
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.rerun()
            
        if st.button("📊 Ver Estadísticas", use_container_width=True):
            st.session_state.show_stats = True
            
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            from services.auth_service import logout_user
            logout_user()
            st.rerun()
    
    # Header de administración
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='margin: 0;'>
                🔧 Administración de <span style='color: #A5A2EC;'>Memorias</span>
            </h1>
            <p style='color: #666; font-size: 1.1em;'>
                Panel de control para gestión avanzada del sistema
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Breadcrumb de navegación
    st.markdown(
        """
        <div style="background: rgba(165, 162, 236, 0.1); padding: 10px 15px; border-radius: 8px; margin: 10px 0; font-size: 0.9em;">
            🧭 <strong>Navegación:</strong> Inicio → <strong>Admin Memorias</strong>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Panel de administración
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Usar el componente de gestión de chats
        chat_manager.admin_chat_management()
    
    with col2:
        st.subheader("📈 Estado del Sistema")
        
        # Métricas del sistema
        st.metric("Usuarios Activos", "15", "+2")
        st.metric("Chats Hoy", "47", "12%")
        st.metric("Tiempo Respuesta", "1.2s", "-0.3s")
        
        st.markdown("---")
        
        # Acciones del sistema
        st.subheader("🛠️ Mantenimiento")
        
        if st.button("🧹 Limpiar Cache", use_container_width=True):
            st.info("Limpiando cache del sistema...")
            
        if st.button("📁 Backup Datos", use_container_width=True):
            st.info("Generando backup de la base de datos...")
            
        if st.button("🔍 Ver Logs", use_container_width=True):
            st.info("Accediendo a logs del sistema...")
    
    # Panel de estadísticas si está activado
    if st.session_state.get('show_stats', False):
        st.markdown("---")
        st.subheader("📊 Estadísticas Detalladas")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Chats", "1,247")
        with col2:
            st.metric("Usuarios Únicos", "89")
        with col3:
            st.metric("Tiempo Promedio", "8.7min")
        
        if st.button("❌ Cerrar Estadísticas"):
            st.session_state.show_stats = False
            st.rerun()
    
    st.markdown("---")
    st.caption("Panel de administración - Solo usuarios autorizados | AltheIA v1.0")

if __name__ == "__main__":
    main()