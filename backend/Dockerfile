# ---------- STAGE 1: Builder ----------
    FROM python:3.11-slim AS builder
    ENV PIP_NO_CACHE_DIR=1 \
        PIP_DISABLE_PIP_VERSION_CHECK=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1
    
    WORKDIR /app
    
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
     && rm -rf /var/lib/apt/lists/*
    
    COPY backend/requirements.txt .
    
    # Usa BuildKit para cachear wheels sin inflar capas
    # DOCKER_BUILDKIT=1 debe estar activo
    RUN --mount=type=cache,target=/root/.cache/pip \
        pip install --no-cache-dir -r requirements.txt
    
    # ---------- STAGE 2: Runtime ----------
    FROM python:3.11-slim
    
    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1
    
    # Dependencias runtime de psycopg/ldap si las necesitas
    RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    
    # Copia paquetes ya instalados del builder
    COPY --from=builder /usr/local /usr/local
    
    # Copia el código fuente
    COPY backend /app
    
    # Usa un usuario no root si quieres, pero instala system-wide
    RUN useradd -m appuser
    USER appuser
    
    EXPOSE 8080
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]