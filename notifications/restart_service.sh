#!/bin/bash
# Script para reiniciar el servicio de notificaciones después de actualizaciones

set -e

echo "=== Reiniciando Servicio de Notificaciones ==="

# Detener proceso actual
echo "1. Deteniendo proceso actual..."
pkill -f "python.*main.py" || echo "No hay proceso corriendo"

# Activar entorno virtual
echo "2. Activando entorno virtual..."
cd ~/Inventario/notifications
source ~/venv/bin/activate

# Pull últimos cambios
echo "3. Obteniendo últimos cambios..."
git pull origin servicediscovery

# Instalar/actualizar dependencias
echo "4. Instalando dependencias..."
pip install -r requirements.txt

# Esperar un momento
sleep 2

# Iniciar servicio
echo "5. Iniciando servicio..."
nohup python main.py > /tmp/notifications.log 2>&1 &

# Esperar que el servicio inicie
sleep 3

# Verificar estado
echo "6. Verificando estado del servicio..."
if curl -k http://localhost:8001/health 2>/dev/null | grep -q "healthy"; then
    echo "✅ Servicio iniciado correctamente"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ Error al iniciar el servicio"
    echo "Últimas líneas del log:"
    tail -20 /tmp/notifications.log
    exit 1
fi

echo "=== Reinicio completado ==="
