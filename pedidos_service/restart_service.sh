#!/bin/bash

# Script de reinicio para el microservicio de Pedidos
# Detiene procesos existentes y reinicia el servicio

set -e

echo "🔄 Reiniciando Pedidos Service..."

# Matar procesos existentes
pkill -f "uvicorn pedidos_service.main" || true
sleep 2

# Iniciar servicio
bash /home/ubuntu/pedidos_service/start_service.sh
