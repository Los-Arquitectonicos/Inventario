#!/bin/bash
# Script para actualizar la configuración de Kong para el servicio de notificaciones
# Ejecutar desde AWS CloudShell

set -e

echo "=========================================="
echo "  Actualizar Ruta de Notificaciones en Kong"
echo "=========================================="

# Obtener IP de Kong
echo "Obteniendo IP de Kong..."
KONG_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*kong*" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

if [ -z "$KONG_IP" ] || [ "$KONG_IP" = "None" ]; then
  echo "❌ No se encontró instancia de Kong"
  exit 1
fi

echo "✅ Kong encontrado: $KONG_IP"

# Obtener IP de notificaciones
echo "Obteniendo IP de notificaciones..."
NOTIF_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*notifications*" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PrivateIpAddress" \
  --output text)

if [ -z "$NOTIF_IP" ] || [ "$NOTIF_IP" = "None" ]; then
  echo "❌ No se encontró instancia de notificaciones"
  exit 1
fi

echo "✅ Notificaciones encontrado: $NOTIF_IP (IP privada)"

echo ""
echo "Actualizando kong.yaml en Kong..."

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@$KONG_IP << ENDSSH
# Verificar el archivo actual
echo "Configuración actual de notifications:"
grep -A 8 "notifications-service" /home/ubuntu/kong.yaml || echo "No encontrado en /home/ubuntu"

# Actualizar strip_path a true
sudo sed -i 's/strip_path: false$/strip_path: true/' /home/ubuntu/kong.yaml

# Verificar el cambio
echo ""
echo "Nueva configuración:"
grep -A 8 "notifications-service" /home/ubuntu/kong.yaml

# Reiniciar Kong para aplicar cambios
echo ""
echo "Reiniciando Kong..."
sudo docker restart \$(sudo docker ps -q --filter "name=kong")

echo "Esperando 5 segundos..."
sleep 5

# Verificar que Kong está corriendo
echo ""
echo "Estado de Kong:"
sudo docker ps --filter "name=kong"
ENDSSH

echo ""
echo "=========================================="
echo "  ✅ Actualización Completada"
echo "=========================================="
echo ""
echo "Prueba el servicio con:"
echo "  curl -k https://$KONG_IP:8443/notifications/health"
echo ""
echo "O ejecuta:"
echo "  python3 test_notifications_service.py"
