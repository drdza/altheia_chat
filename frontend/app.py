import streamlit as st
import requests
from datetime import datetime
from services.auth_service import login_user, is_admin, logout_user
from shared import utils
from components import user_tools, chats_user, admin_panel

# --- Configuración inicial ---
st.set_page_config(
    page_title="AltheIA - Inicio", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Configurar navegación personalizada ---
utils.setup_custom_navigation()

# --- Estado inicial global (solo se ejecuta una vez) ---
default_keys = {
    "access_token": None,
    "user_id": None,
    "rephrased": None,
    "style": None,
    "session": requests.Session(),
    "chat_id": None,
    "chat_history": [],
    "copied": None,
    "new_chat_mode": False,
    "show_chat_management": False
}
for k, v in default_keys.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Cargar estilos institucionales
utils.load_css("frontend/assets/styles.css")
utils.apply_dynamic_background(bool(st.session_state.user_id))
  
# --- Sidebar login/logout ---
with st.sidebar:
    st.logo("frontend/assets/img/altheia-logo-black.png", size="large")
    login_ico = utils.get_base64_image("frontend/assets/img/login-ico.png")

    col1, col2 = st.columns([6,2], vertical_alignment='center')  
    with col1:
        sidebar_header = st.empty()
    
    sidebar_header.markdown(f"""
        <div class="stLogin">
            <img src="data:image/png;base64,{login_ico}" style="width: 25px; height: 25px; vertical-align: middle"; > Login
        </div>""", unsafe_allow_html=True)

    if st.session_state.user_id:
        fullname = st.session_state.user_id.get("username")
        username = utils.get_simple_username(fullname)         
        with col1:
            sidebar_header.markdown(
                f"""
                <div class="welcome-box">👋 Bienvenid@ </div>
                <div class="welcome-box user">{username}</div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            if st.button("🔓", 
                key="logout_button", 
                use_container_width=False,
                help ="Cerrar Sesion",                
            ):
                logout_user()
                st.rerun()

        # --- Navegación personalizada ---
        utils.render_custom_navigation("Inicio")

        # Chats Previos
        chats_user.get_user_chats() 

        # Herramientas generales
        user_tools.load_user_options()

        # Herramientas administrativas
        if is_admin(st.session_state.user_id):
            admin_panel.admin_tools()

    else:
        user_ico = utils.get_base64_image("frontend/assets/img/user-ico.png")
        st.markdown(f"""
            <div class="stFieldName">
                <img src="data:image/png;base64,{user_ico}" style="width: 25px; height: 25px; vertical-align: middle";> Usuario
            </div>""", unsafe_allow_html=True)
        username = st.text_input("Usuario", label_visibility='collapsed', key="username_input")

        key_ico = utils.get_base64_image("frontend/assets/img/key-ico.png")
        st.markdown(f"""
            <div class="stFieldName">
                <img src="data:image/png;base64,{key_ico}" style="width: 25px; height: 25px; vertical-align: middle";> Contraseña
            </div>""", unsafe_allow_html=True)

        # --- Nueva lógica: función de login compartida ---
        def handle_login():
            user_id = login_user(st.session_state.username_input, st.session_state.password_input)
            if user_id:
                st.session_state.user_id = user_id                
                st.rerun()

        # Input con on_change (detecta Enter)
        password = st.text_input(
            "Contraseña",
            type="password",
            key="password_input",
            label_visibility='collapsed',
            on_change=handle_login  # Ejecuta login al presionar Enter
        )

        # Botón Ingresar
        if st.button("Ingresar", key="login_button", use_container_width=True):
            handle_login()

# --- Contenido principal de la página de inicio ---
if st.session_state.user_id:
    # Si el usuario está logueado, mostrar dashboard de inicio
    st.markdown(
        """
        <div class='stTitleChat'><h1>
            Bienvenido a Althe<span style='color: #A5A2EC;'>IA</span>
        </h1></div>
        """,
        unsafe_allow_html=True
    )
    st.divider()
    
    # Dashboard de acciones rápidas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div style='text-align: center; padding: 2rem 1rem; background: rgba(165, 162, 236, 0.1); border-radius: 10px; border: 1px solid rgba(165, 162, 236, 0.3);'>
                <div style='font-size: 3em; margin-bottom: 1rem;'>💬</div>
                <h3>Chat Principal</h3>
                <p>Inicia una conversación con tu asistente de IA</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Ir al Chat", key="go_chat", use_container_width=True):
            st.switch_page("pages/01_Chat_Principal.py")
    
    with col2:
        st.markdown(
            """
            <div style='text-align: center; padding: 2rem 1rem; background: rgba(165, 162, 236, 0.1); border-radius: 10px; border: 1px solid rgba(165, 162, 236, 0.3);'>
                <div style='font-size: 3em; margin-bottom: 1rem;'>🗂️</div>
                <h3>Gestionar Chats</h3>
                <p>Administra tus conversaciones anteriores</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Gestionar", key="go_manage", use_container_width=True):
            st.session_state.show_chat_management = True
            st.rerun()
    
    with col3:
        st.markdown(
            """
            <div style='text-align: center; padding: 2rem 1rem; background: rgba(165, 162, 236, 0.1); border-radius: 10px; border: 1px solid rgba(165, 162, 236, 0.3);'>
                <div style='font-size: 3em; margin-bottom: 1rem;'>🔧</div>
                <h3>Administración</h3>
                <p>Herramientas avanzadas del sistema</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Panel Admin", key="go_admin", use_container_width=True):
            st.switch_page("pages/02_Admin_Memorias.py")
    
    # Estadísticas rápidas
    st.markdown("---")
    st.subheader("📊 Resumen Rápido")
    
    try:
        chats = st.session_state.get('user_chats', [])
        total_chats = len(chats)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chats Activos", total_chats)
        with col2:
            st.metric("Disponibles", f"{20 - total_chats}")
        with col3:
            usage = (total_chats / 20) * 100 if 20 > 0 else 0
            st.metric("Uso", f"{usage:.1f}%")
        
        st.progress(usage / 100)
        
    except:
        st.info("Cargando estadísticas...")
    
    # Mostrar modal de gestión si está activado
    if st.session_state.get('show_chat_management', False):
        chats_user.show_chat_management_modal()

else:
    # Página de landing para usuarios no logueados
    logo_base64 = utils.get_base64_image("frontend/assets/img/altheia-logo-white.png")
    hora = datetime.now().hour
    saludo = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches"

    st.markdown(
        f"""
        <div class="welcome-overlay">
            <div class="welcome-overlay-title">
                <span class="welcome-overlay-color">{saludo}</span>, te damos la bienvenida a
            </div>
            <div class="welcome-overlay-logo"><img src="data:image/png;base64,{logo_base64}"></div>
            <span class="welcome-overlay-msg">
                <b>Soy tu asistente de IA.</b>
                Puedo ayudarte a organizar tu día, buscar información, redactar textos o resolver dudas.</p>
                <b>¿Empezamos? 🚀</b> Solo inicia sesión desde el menú lateral para comenzar.</p>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )