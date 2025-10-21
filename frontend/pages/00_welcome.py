# frontend/pages/00_welcome.py
import streamlit as st
from datetime import datetime
from services.auth_service import login_user
from shared import utils

# Configurar la página
st.set_page_config(
    page_title="AltheIA - Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"  # Sin sidebar
)

def main():
    # Configuración
    utils.load_css("frontend/assets/styles.css")
    utils.apply_dynamic_background(False)
    
    # Contenido principal - Solo formulario de login
    render_login_page()

def render_login_page():
    """Renderiza solo la página de login"""
    logo_base64 = utils.get_base64_image("frontend/assets/img/altheia-logo-white.png")
    hora = datetime.now().hour
    saludo = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches"
    
    # Layout centrado del login
    
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
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
        
    # Formulario de login
    with st.form("login_form"):
        st.divider()

        username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
         
        if st.form_submit_button("🚀 Ingresar", use_container_width=True):
            if username and password:
                user_id = login_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id       
                    st.switch_page("pages/01_chat.py")                 
                else:
                    st.error("Credenciales incorrectas")
            else:
                st.warning("Por favor ingresa usuario y contraseña")

if __name__ == "__main__":
    main()