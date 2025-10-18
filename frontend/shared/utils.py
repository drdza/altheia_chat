# shared/utils.py
import streamlit as st
import base64
from pathlib import Path
 
def get_base64_image(path):
    with open(path, "rb") as img_file: 
        return base64.b64encode(img_file.read()).decode()
 
def get_base64_font(path):
    with open(path, "rb") as font_file: 
        return base64.b64encode(font_file.read()).decode()

def load_css(file_name: str):
    try:
        user_b64 = get_base64_image("frontend/assets/img/user-ico.png")
        bot_b64 = get_base64_image("frontend/assets/img/altheia-ico.png")

        # --- Fuentes personalizadas ---
        fonts = [
            ("Blinker-Bold", "frontend/assets/fonts/Blinker-Bold.ttf", "truetype"),        
            ("Blinker-Regular", "frontend/assets/fonts/Blinker-Regular.ttf", "truetype"),
             ("Blinker-Light", "frontend/assets/fonts/Blinker-Light.ttf", "truetype"),
            ("Blinker-Thin", "frontend/assets/fonts/Blinker-Thin.ttf", "truetype"),
        ]

        font_faces = ""
        for name, path, fmt in fonts:
            try:
                font_b64 = get_base64_font(path)
                font_faces += f"""
                @font-face {{
                    font-family: '{name}';
                    src: url(data:font/{fmt};base64,{font_b64}) format('{fmt}');
                    font-weight: normal;
                    font-style: normal;
                }}            
                """
            except FileNotFoundError:
                st.warning(f"⚠️ Fuente no encontrada: {path}")     
    
        with open(file_name, encoding="utf-8") as f:
            css = f.read()

        css = css.replace("USER_AVATAR_B64", user_b64)
        css = css.replace("BOT_AVATAR_B64", bot_b64)
            
        return st.markdown(f"<style>{font_faces}{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        return None

def get_simple_username(full_username: str) -> str:
    """
    Extrae nombre simplificado usando diferentes estrategias.
    """
    if not full_username or not full_username.strip():
        return full_username
    
    # Limpiar y dividir
    parts = full_username.strip().split()
    
    if len(parts) <= 2:
        return full_username.capitalize()
    
    # Estrategia 1: Buscar patrones comunes
    # Si hay exactamente 4 partes, probablemente es: Nombre1 Nombre2 Apellido1 Apellido2
    if len(parts) == 4:
        return f"{parts[0].capitalize()} {parts[2].capitalize()}"
    
    # Estrategia 2: Primer nombre + último apellido (por defecto)
    return f"{parts[0].capitalize()} {parts[-1].capitalize()}"        

def apply_dynamic_background(is_logged_in: bool):
    """Aplica un fondo distinto según si el usuario está logueado o no."""
    if not is_logged_in:
        bg_path = Path("frontend/assets/img/background-altheia.jpg")
        # Convertir imagen a base64
        image_base64 = base64.b64encode(bg_path.read_bytes()).decode()
        css_insert = f"""background-image: url("data:image/png;base64,{image_base64}");"""
    else:
        css_insert = 'background-color: inherit;' 

    # Inyectar CSS dinámico
    st.markdown(
        f"""
        <style>
        .stApp {{
            {css_insert}
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            transition: background 0.6s ease-in-out;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def setup_custom_navigation():
    """
    Configura navegación personalizada y oculta la automática
    """
    custom_nav_css = """
    <style>
        /* Ocultar navegación automática de Streamlit */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Ocultar header por defecto */
        header[data-testid="stHeader"] {
            display: none;
        }
        
        /* Navegación personalizada en sidebar */
        .custom-nav {
            margin: 20px 0;
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .custom-nav h4 {
            margin: 0 0 15px 0;
            color: #A5A2EC;
            font-size: 1.1em;
            font-weight: 600;
        }
        .custom-nav-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            margin: 8px 0;
            background: rgba(165, 162, 236, 0.1);
            border-radius: 8px;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        .custom-nav-item:hover {
            background: rgba(165, 162, 236, 0.2);
            transform: translateX(5px);
            border-color: #A5A2EC;
            text-decoration: none;
            color: white;
        }
        .nav-icon {
            margin-right: 10px;
            font-size: 1.1em;
        }
        .nav-active {
            background: rgba(165, 162, 236, 0.25) !important;
            border-color: #A5A2EC !important;
            font-weight: 600;
        }
    </style>
    """
    st.markdown(custom_nav_css, unsafe_allow_html=True)

def render_custom_navigation(current_page="Inicio"):
    """
    Renderiza navegación personalizada en el sidebar
    """
    nav_items = [
        {"icon": "🏠", "label": "Inicio", "page": "/", "target": "_self"},
        {"icon": "💬", "label": "Chat Principal", "page": "/pages/01_Chat_Principal.py", "target": "_self"},
        {"icon": "🔧", "label": "Admin Memorias", "page": "/pages/02_Admin_Memorias.py", "target": "_self"},
    ]
    
    nav_html = """
    <div class="custom-nav">
        <h4>🧭 Navegación</h4>
    """
    
    for item in nav_items:
        active_class = "nav-active" if item["label"] == current_page else ""
        nav_html += f"""
        <a href="{item['page']}" target="{item['target']}" class="custom-nav-item {active_class}">
            <span class="nav-icon">{item['icon']}</span>
            {item['label']}
        </a>
        """
    
    nav_html += "</div>"
    
    st.markdown(nav_html, unsafe_allow_html=True)