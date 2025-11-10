# frontend/components/user_tools.py

import streamlit as st
from services import api

def rephrase_option():
        # Constante de estilos (fuera de la función si es posible)
        STYLES = {
            "Formal breve": "que suene formal, breve y claro",
            "Técnico": "que sea técnico y específico",
            "Amigable": "que suene empático y claro", 
            "Estándar": "redactado de forma correcta para soporte técnico",
            "Personalizada": "personalizada"
        }                
        # Opción de Reformulación
        st.session_state.rephrased = st.checkbox("✍️ Reformular", value=st.session_state.rephrased, width="stretch")
         
        if st.session_state.rephrased:
            style_choice = st.selectbox("Estilo de la reformulación", list(STYLES.keys()))
            
            if STYLES[style_choice] == "personalizada":
                st.session_state.style = st.text_area(
                    "Estilo personalizado",
                    placeholder="Describe una característica extra o especial para tu reformulación",
                    value=st.session_state.style
                )
            else:
                st.session_state.style = STYLES[style_choice]
                st.caption(st.session_state.style)

def upload_user_file():
    st.caption("#### 📁 Subir archivo para consultas personales")
        
    file = st.file_uploader("Elige un documento (txt, md, pdf, docx, xlsx)...", type=["txt", "md", "pdf", "docx", "xlsx"], label_visibility="collapsed")
    
    if st.button("🔗 Cargar Archivo", width="stretch") and file:
        ok = api.upload_user_file(file)
        if ok:
            st.toast("Documento cargado correctamente", icon = '✅', duration=5)
        else:
            st.toast("Ocurrió un error al subir el documento", icon = '❌', duration=5)
