#!/bin/bash
# Script para reiniciar el servidor Django después de actualizaciones

set -e

echo "=== Reiniciando Servidor Django ==="

# Detener proceso actual
echo "1. Deteniendo proceso actual..."
pkill -f "python.*manage.py.*runserver" || echo "No hay proceso corriendo"

# Activar entorno virtual
echo "2. Activando entorno virtual..."
cd ~/app/Inventario/ProvesiWMS
source venv/bin/activate

# Pull últimos cambios
echo "3. Obteniendo últimos cambios..."
git pull origin servicediscovery

# Instalar/actualizar dependencias
echo "4. Instalando dependencias..."
pip install -r requirements.txt

# Aplicar migraciones
echo "5. Aplicando migraciones..."
python manage.py migrate

# Esperar un momento
sleep 2

# Iniciar servidor Django
echo "6. Iniciando servidor Django..."
nohup python manage.py runserver 0.0.0.0:8080 > /tmp/django.log 2>&1 &

# Esperar que el servidor inicie
sleep 3

# Verificar estado
echo "7. Verificando estado del servidor..."
if curl -s http://localhost:8080/inventario/ 2>/dev/null | grep -q "text/html\|HTTP"; then
    echo "✅ Servidor Django iniciado correctamente"
    ps aux | grep "python.*manage.py.*runserver" | grep -v grep
else
    echo "❌ Error al iniciar el servidor"
    echo "Últimas líneas del log:"
    tail -20 /tmp/django.log
    exit 1
fi

echo "=== Reinicio completado ==="
