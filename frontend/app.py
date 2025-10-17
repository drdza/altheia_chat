import streamlit as st
import requests
from datetime import datetime
from services.auth_service import login_user, is_admin, logout_user
from shared import utils
from components.chat_ui import chat_interface, chat_interface_stream
from components import user_tools, chats_user, admin_panel

# --- Configuración inicial ---
st.set_page_config(page_title="Chat with AltheIA", layout="centered")

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
    "new_chat_mode": False
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

        # Si ya se logueó correctamente, forzar rerun aquí (fuera del callback)
        if st.session_state.user_id:
            st.rerun()

# --- Si ya está logueado ---
if st.session_state.user_id:
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

else:
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
