# frontend/components/admin_panel.py

import streamlit as st
from services.api import upload_public_file, reset_vectorstore

def admin_tools():
    #st.subheader("🛠️ Herramientas de administración")  
    with st.expander("🛠️ Administración"):
        st.write("#### 📤 Documentos públicos")
        
        file = st.file_uploader("Selecciona un archivo público", type=["txt","md", "pdf", "docx", "xlsx"], key="admin_upload")
        
        if st.button("📤 Subir documento", width="stretch") and file:
            ok = upload_public_file(file)
            if ok:
                st.toast("Documento cargado correctamente", icon = '✅', duration=5)
            else:
                st.toast("Ocurrió un error al subir el documento", icon = '❌', duration=5)

        st.write("---")
        
        if st.button("🗑️ Reset Milvus Collection", help="Esta acción eliminará toda la colección vectorial", width="stretch"):
            result = reset_vectorstore()
            if result["status"] == 'ok':
                st.toast(result["message"], icon = '✅', duration=5)
            else:
                st.toast(result["message"], icon = '❌', duration=5)                