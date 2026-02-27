FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (psycopg v3 suele funcionar sin build deps; si usas psycopg2 podrías necesitar gcc)
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Por defecto no arranca nada; compose define el command