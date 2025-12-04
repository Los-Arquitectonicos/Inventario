#!/bin/bash
# Script para actualizar la configuración de Kong - Ejecutar EN la instancia de Kong
# Copiar este script a la instancia de Kong y ejecutarlo allí

set -e

echo "=========================================="
echo "  Actualizar Ruta de Notificaciones"
echo "=========================================="

# Verificar que estamos en la instancia correcta
if [ ! -f /home/ubuntu/kong.yaml ]; then
    echo "❌ No se encuentra kong.yaml en /home/ubuntu/"
    echo "   ¿Estás ejecutando esto en la instancia de Kong?"
    exit 1
fi

echo "Configuración actual de notifications:"
grep -A 8 "notifications-service" /home/ubuntu/kong.yaml

echo ""
echo "Actualizando strip_path a true..."

# Crear backup
sudo cp /home/ubuntu/kong.yaml /home/ubuntu/kong.yaml.backup

# Actualizar la configuración
# Buscar la línea "strip_path: false" que está después de "notifications-route"
sudo sed -i '/notifications-route/,/strip_path: false/ {
    s/strip_path: false/strip_path: true/
}' /home/ubuntu/kong.yaml

echo ""
echo "Nueva configuración:"
grep -A 8 "notifications-service" /home/ubuntu/kong.yaml

echo ""
echo "Reiniciando Kong..."
sudo docker restart $(sudo docker ps -q --filter "name=kong")

echo ""
echo "Esperando 5 segundos para que Kong inicie..."
sleep 5

echo ""
echo "Estado de Kong:"
sudo docker ps --filter "name=kong"

echo ""
echo "=========================================="
echo "  ✅ Actualización Completada"
echo "=========================================="
echo ""
echo "Verifica con:"
echo "  curl http://localhost:8000/notifications/health"
