
# 🤖 AltheIA Chat

**AltheIA** es un servicio de agentes impulsados con inteligencia artificial con el objetivo de mejorar la experiencia de los usuarios dentro de **Grupo Reyes**, proporcionando respuestas rápidas, contextuales y útiles, tanto a preguntas generales como a consultas basadas en información interna.

---

## 🧠 ¿Qué es AltheIA Chat?

AltheIA Chat es un **asistente conversacional empresarial** desarrollado por el equipo de **Innovación y Negocios**, con las siguientes funcionalidades principales:

- 📚 **Acceso a una base de conocimientos empresarial**, administrada por el equipo de Innovación y Negocios.
- 📁 **Espacio vectorial privado para cada usuario**, donde pueden cargar sus propios archivos (Word, Excel, TXT, Markdown, PowerPoint) para generar insights personalizados.
- 🧾 **Integración con sistemas internos** como el agente SQL que permite consultar datos en tiempo real sobre tickets y solicitudes, reduciendo la necesidad de contactar al Centro de Atención a Usuarios (CAU).

---

## 🚀 Funcionalidades Clave

### 🔍 Búsqueda híbrida
Permite a los usuarios hacer preguntas sobre documentos empresariales o personales, combinando RAG (Retrieval-Augmented Generation) con embeddings y funciones semánticas.

### 🧩 Espacio vectorial personalizado
Cada usuario tiene un espacio de vectores separado donde puede subir documentos propios para obtener respuestas contextuales directamente de sus archivos.

### 🛠️ Conexión con SQL Interno
El agente puede consultar una base de datos interna de tickets y dar seguimiento a consultas sin intervención humana, integrándose con los procesos del CAU.

---

## 🗂️ Tipos de archivos soportados

- `.docx`
- `.xlsx`
- `.txt`
- `.md`
- `.pptx`

Todos estos formatos pueden ser cargados y analizados por el agente.

---

## 🏗️ Arquitectura general (resumen)

```mermaid
graph LR
    A[Usuario] -->|Pregunta| B[AltheIA Chat]
    B --> C[Motor de IA (LLM)]
    C --> D[Base de conocimientos general]
    C --> E[Espacio vectorial por usuario]
    C --> F[Agente SQL interno]
    F --> G[Base de datos de tickets]
```

---

## 📦 Tecnologías utilizadas

- **Python**
- **LangGraph** para orquestación de agentes
- **Milvus** o similar para espacios vectoriales
- **meta/LlaMa-3.1-70B-Instruct-GPTQ-INT4** para el modelo base
- **PostgreSQL** para consultas internas
- **Streamlit** frontend

---

## 🧪 Estado actual del proyecto

- [x] Soporte para múltiples formatos de archivo
- [x] Integración con agente SQL
- [x] Espacio vectorial por usuario
- [ ] Autenticación empresarial con AD
- [ ] Dashboard de métricas e interacción

---

## 👥 Equipo

Proyecto desarrollado por el equipo de **iNN\Inteligencia Empresarial** de **Grupo Reyes**.

---

## 📄 Licencia

Este proyecto es propiedad de Grupo Reyes. Todos los derechos reservados. 2025

---

## 📬 Contacto

Para soporte o sugerencias:

📧 inteligencia.empresarial@reyma.com.mx  
📌 Área: Inteligencia Empresarial
