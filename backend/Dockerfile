# Imagen base ligera de Python
FROM python:3.11-slim

# Definir variables de entorno básicas
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Crear directorio de trabajo
WORKDIR /app

# Copiar los requirements específicos del backend
COPY backend/requirements.txt /app/requirements.txt

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copiar el código fuente del backend
COPY backend /app

# Exponer el puerto de FastAPI
EXPOSE 8080

# Comando de inicio (usamos uvicorn directamente)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
