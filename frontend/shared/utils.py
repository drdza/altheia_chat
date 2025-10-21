# shared/utils.py
import streamlit as st
import base64
from pathlib import Path

from sympy import false
 
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

def get_simple_username(full_username: str, format_type: str = "first_last") -> str:
    """
    Extrae nombre simplificado usando diferentes formatos.
    
    Args:
        full_username: Nombre completo del usuario
        format_type: Tipo de formato a devolver:
            - "first_only": Solo primer nombre
            - "first_last": Primer nombre y primer apellido (default)
            - "full": Nombre completo capitalizado
    
    Returns:
        str: Nombre formateado según el tipo solicitado
    """
    if not full_username or not full_username.strip():
        return full_username
    
    # Limpiar y dividir el nombre
    parts = [part.strip() for part in full_username.split() if part.strip()]
    
    if not parts:
        return full_username
    
    # Aplicar el formato solicitado
    if format_type == "first_only":
        return parts[0].capitalize()
    
    elif format_type == "first_last":
        if len(parts) >= 2:
            return f"{parts[0].capitalize()} {parts[-2].capitalize()}"
        else:
            return parts[0].capitalize()
    
    elif format_type == "full":
        return " ".join(part.capitalize() for part in parts)
    
    else:
        # Por defecto, usar first_last
        if len(parts) >= 2:
            return f"{parts[0].capitalize()} {parts[-1].capitalize()}"
        else:
            return parts[0].capitalize()


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
            padding: 8px 12px;
            margin: 0 0 12px;
            background: rgba(165, 162, 236, 0.1);
            border-radius: 8px;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
            border: 1px solid transparent;
            height: 38px;
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
    Renderiza navegación personalizada usando columnas de Streamlit
    """
    # Definir items de navegación (sin Cerrar Sesión)
    nav_items = [        
        {"icon": "💬", "label": "Chat", "page": "pages/01_chat.py"}, 
        {"icon": "🗂️", "label": "Opciones", "page": "pages/02_chat_manager.py"},        
    ]
    
    st.sidebar.subheader("🧭 Navegación")
    
    # Crear filas de 2 columnas
    for i in range(0, len(nav_items), 2):
        cols = st.sidebar.columns(2)
        
        for j in range(2):
            if i + j < len(nav_items):
                item = nav_items[i + j]
                with cols[j]:
                    if item["label"] == current_page:
                        # Item activo - deshabilitado
                        st.button(
                            f"{item['icon']} {item['label']}", 
                            key=f"nav_{item['label']}",
                            disabled=True,
                            use_container_width=True,
                            help=item["label"]
                        )
                    else:
                        # Item inactivo - clickeable
                        if st.button(
                            f"{item['icon']} {item['label']}", 
                            key=f"nav_{item['label']}",
                            use_container_width=True,
                            help=item["label"]
                        ):
                            st.switch_page(item["page"])
    
def _render_custom_navigation(current_page="Inicio"):
    """
    Renderiza navegación personalizada en el sidebar usando componentes de Streamlit
    """
    # Definir items de navegación
    nav_items = [
        {"icon": "🏠", "label": "Inicio", "page": "pages/00_welcome.py", "target": "_self"},
        {"icon": "💬", "label": "Chat", "page": "pages/01_chat.py", "target": "_self"},
        {"icon": "🚀", "label": "Conversaciones", "page": "pages/02_chat_manager.py", "target": "_self"},
        {"icon": "🚪", "label": "Cerrar Sesión", "page": "pages/03_logout.py", "target": "_self"},
    ]
    
    st.sidebar.subheader("☰ Menú")

    cols =st.col
    # Renderizar cada item usando st.markdown individualmente
    for item in nav_items:
        active_class = "nav-active" if item["label"] == current_page else ""
        
        # Usar st.link_button para funcionalidad real o st.markdown para estilo
        if item["label"] == current_page:
            st.sidebar.markdown(
                f"""
                <div class="custom-nav-item {active_class}">
                    <span class="nav-icon">{item['icon']}</span>
                    {item['label']}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            if st.sidebar.button(
                f"{item['icon']} {item['label']}", 
                key=f"nav_{item['label']}",
                use_container_width=True                                
            ):
                st.switch_page(item["page"])          