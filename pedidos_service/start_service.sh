#!/bin/bash

# Script de inicio para el microservicio de Pedidos
# Ubuntu 24.04

set -e

echo "🚀 Iniciando Pedidos Service..."

# Directorio del servicio
SERVICE_DIR="/home/ubuntu/pedidos_service"
cd "$SERVICE_DIR"

# Activar entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Iniciar servicio
echo "✅ Iniciando aplicación en puerto ${SERVICE_PORT:-8002}..."
python3 -m uvicorn pedidos_service.main:app \
    --host 0.0.0.0 \
    --port ${SERVICE_PORT:-8002} \
    --log-level ${LOG_LEVEL:-info}
