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


echo "=== Reinicio completado ==="
