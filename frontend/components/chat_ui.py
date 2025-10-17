# frontend/components/chat_ui.py
import uuid
import streamlit as st
from shared import utils
from services.api import chat_with_bot, chat_with_bot_stream, rephrase_text


def chat_interface():

    print(f"[START] Chat ID: {st.session_state.chat_id}")    
    #st.write("#### 🧠 Chat general (con documentos públicos o tus propios archivos)")

    for msg in st.session_state.chat_history:        
        st.chat_message(msg["role"]).markdown(msg["content"])
        
    if user_input:= st.chat_input(""):
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
 
        try:
            if st.session_state.rephrased:
                answer = rephrase_text(user_input, st.session_state.style)
            else:
                chat_response = chat_with_bot(user_input, st.session_state.chat_id)
                answer = chat_response["answer"]
            

            st.chat_message("assistant").markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer}) 
            
            chat_id_from_backend = chat_response["chat_id"]
            st.session_state.chat_id = chat_id_from_backend

            
        except Exception as e:
            st.chat_message("assistant").markdown(f"⚠️ Error: {e}")
    
    print(f"[END] Chat ID: {st.session_state.chat_id}")            
                        

def chat_interface_stream():
    # Estado para el streaming
    if "streaming_content" not in st.session_state:
        st.session_state.streaming_content = ""
    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = False

    print(f"[START] Chat ID: {st.session_state.chat_id}")    

    # Mostrar historial de mensajes
    for msg in st.session_state.chat_history:        
        st.chat_message(msg["role"]).markdown(msg["content"])
    
    # Mostrar contenido en streaming si está activo
    if st.session_state.is_streaming and st.session_state.streaming_content:
        st.chat_message("assistant").markdown(
            st.session_state.streaming_content + "▌"
        )
        
    # Input de chat
    if user_input := st.chat_input("Escribe tu mensaje..."):
        # Limpiar estado de streaming anterior
        st.session_state.streaming_content = ""
        st.session_state.is_streaming = False
        
        # Mostrar mensaje del usuario
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
 
        try:
            if st.session_state.rephrased:
                # Modo rephrase (sin streaming)
                answer = rephrase_text(user_input, st.session_state.style)
                st.chat_message("assistant").markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                
            else:
                # Modo chat normal CON streaming
                st.session_state.is_streaming = True
                
                # Contenedor para el stream
                stream_placeholder = st.empty()
                full_response = ""
                chat_id_from_backend = None
                
                # Procesar stream
                for chunk in chat_with_bot_stream(user_input, st.session_state.chat_id):
                    if "error" in chunk:
                        st.error(f"Error: {chunk['error']}")
                        break
                    
                    # Actualizar chat_id si viene en el primer chunk
                    if "chat_id" in chunk and not chat_id_from_backend:
                        chat_id_from_backend = chunk["chat_id"]
                        st.session_state.chat_id = chat_id_from_backend
                    
                    # Acumular contenido
                    if "content" in chunk and chunk["content"]:
                        full_response += chunk["content"]
                        st.session_state.streaming_content = full_response
                        
                        # Actualizar en tiempo real
                        stream_placeholder.chat_message("assistant").markdown(
                            full_response + "▌"
                        )
                
                # Cuando termina el stream
                st.session_state.is_streaming = False
                st.session_state.streaming_content = ""
                
                # Guardar en historial solo si hay respuesta
                if full_response.strip():
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": full_response
                    })
                    
                    # Forzar rerun para mostrar mensaje final sin cursor
                    st.rerun()
            
        except Exception as e:
            st.session_state.is_streaming = False
            st.session_state.streaming_content = ""
            st.chat_message("assistant").markdown(f"⚠️ Error: {e}")
    
    print(f"[END] Chat ID: {st.session_state.chat_id}")