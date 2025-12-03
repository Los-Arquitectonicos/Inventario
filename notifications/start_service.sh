#!/bin/bash
# Script simple para iniciar el servicio de notificaciones

echo "=== Iniciando Servicio de Notificaciones ==="

# Ir al directorio correcto
cd ~/Inventario/notifications

# Verificar que existe el virtualenv
if [ ! -d "venv" ]; then
    echo "❌ No existe el virtualenv. Creándolo..."
    python3 -m venv venv
    ~/Inventario/notifications/venv/bin/pip install --upgrade pip setuptools wheel
    ~/Inventario/notifications/venv/bin/pip install -r requirements.txt
fi

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Detener proceso anterior si existe
pkill -f "python.*main.py" 2>/dev/null || true

# Iniciar servicio
echo "Iniciando FastAPI en puerto 8001..."
nohup ~/Inventario/notifications/venv/bin/python3 main.py > /home/ubuntu/notifications.log 2>&1 &

sleep 3

# Verificar
if ps aux | grep -v grep | grep "python.*main.py" > /dev/null; then
    echo "✅ Servicio iniciado"
    echo "Ver logs: tail -f /home/ubuntu/notifications.log"
    echo "Probar: curl http://localhost:8001/health"
else
    echo "❌ Error al iniciar"
    tail -20 /home/ubuntu/notifications.log
fi
