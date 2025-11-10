FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copiar requirements
COPY frontend/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copiar TODO el proyecto
COPY . .

# Exponer puerto
EXPOSE 8501

# Comando de inicio desde el subdirectorio frontend
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]