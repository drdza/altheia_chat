# ---------- STAGE 1: Builder ----------
    FROM python:3.11-slim AS builder

    WORKDIR /app
    
    # Instalar herramientas de compilación solo aquí
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev
    
    # Copiar requirements y compilarlos
    COPY backend/requirements.txt .
    RUN pip install --user --no-cache-dir -r requirements.txt
    
    
    # ---------- STAGE 2: Runtime ----------
    FROM python:3.11-slim
    
    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PATH=/home/appuser/.local/bin:$PATH
    
    # Crear usuario sin privilegios
    RUN useradd -m appuser
    
    WORKDIR /app
    
    # Copiar dependencias ya compiladas desde builder
    COPY --from=builder /root/.local /home/appuser/.local
    
    # Copiar el código fuente
    COPY backend /app
    
    # Cambiar a usuario no root
    USER appuser
    
    EXPOSE 8080
    
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
    