#!/bin/bash
# Script para reiniciar el servidor Django después de actualizaciones

set -e

# Variable para el nombre de la rama
BRANCH="${1:-servicediscovery}"

echo "=== Reiniciando Servidor Django ==="
echo "Rama: $BRANCH"

# Detener proceso actual
echo "1. Deteniendo proceso actual..."
pkill -f "python.*manage.py.*runserver" || echo "No hay proceso corriendo"
sleep 1

# Activar entorno virtual
echo "2. Activando entorno virtual..."
cd ~/app/Inventario/ProvesiWMS
source venv/bin/activate

# Pull últimos cambios
echo "3. Obteniendo últimos cambios..."
git pull origin $BRANCH

# Instalar/actualizar dependencias
echo "4. Instalando dependencias..."
pip install -q -r requirements.txt

# Aplicar migraciones
echo "5. Aplicando migraciones..."
python3 manage.py migrate --noinput

# Iniciar servidor Django en background
echo "6. Iniciando servidor Django..."
nohup python3 manage.py runserver 0.0.0.0:8080 > /tmp/django.log 2>&1 &

# Esperar que el servidor inicie
echo "7. Esperando inicio del servidor..."
sleep 5

# Verificar que el proceso está corriendo
if pgrep -f "python.*manage.py.*runserver" > /dev/null; then
    echo "Servidor Django iniciado correctamente en puerto 8080"
    echo "Proceso:"
    ps aux | grep "python.*manage.py.*runserver" | grep -v grep | head -1
    echo ""
    echo "Ver logs: tail -f /tmp/django.log"
else
    echo "Error: El servidor no está corriendo"
    echo "Últimas líneas del log:"
    tail -30 /tmp/django.log
    exit 1
fi

echo "=== Reinicio completado ==="
