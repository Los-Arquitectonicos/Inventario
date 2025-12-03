#!/bin/bash
# Script para reiniciar el servicio de notificaciones después de actualizaciones

set -e

echo "=== Reiniciando Servicio de Notificaciones ==="

# Detener proceso actual
echo "1. Deteniendo proceso actual..."
pkill -f "python.*main.py" || echo "No hay proceso corriendo"

# Activar entorno virtual y actualizar
echo "2. Actualizando código..."
cd ~/Inventario/notifications
git pull origin servicediscovery

# Instalar/actualizar dependencias
echo "3. Instalando dependencias..."
~/Inventario/notifications/venv/bin/pip install -r requirements.txt

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Esperar un momento
sleep 2

# Iniciar servicio usando ruta completa del Python del virtualenv
echo "4. Iniciando servicio..."
nohup ~/Inventario/notifications/venv/bin/python3 main.py > /home/ubuntu/notifications.log 2>&1 &

# Esperar que el servicio inicie
sleep 3

# Verificar estado
echo "5. Verificando estado del servicio..."
sleep 3
if curl -s http://localhost:8001/health 2>/dev/null | grep -q "healthy"; then
    echo "✅ Servicio iniciado correctamente"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ Error al iniciar el servicio"
    echo "Últimas líneas del log:"
    tail -20 /home/ubuntu/notifications.log
    exit 1
fi

echo "=== Reinicio completado ==="
