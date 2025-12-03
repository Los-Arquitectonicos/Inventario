#!/bin/bash
# Script para diagnosticar y reiniciar el servicio de notificaciones
# Ejecutar desde AWS CloudShell

set -e

echo "=========================================="
echo "  Diagnóstico Servicio de Notificaciones"
echo "=========================================="

# Obtener IP de la instancia de notificaciones
echo "Obteniendo IP de instancia de notificaciones..."
NOTIF_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=notifications-instance" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

if [ -z "$NOTIF_IP" ] || [ "$NOTIF_IP" = "None" ]; then
  echo "❌ No se encontró instancia de notificaciones en ejecución"
  exit 1
fi

echo "✅ Instancia encontrada: $NOTIF_IP"

echo ""
echo "=========================================="
echo "  Verificando estado del contenedor"
echo "=========================================="

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@$NOTIF_IP << 'ENDSSH'
echo "Estado de contenedores Docker:"
sudo docker ps -a | grep -E "CONTAINER|notification" || echo "No hay contenedores de notificaciones"

echo ""
echo "Verificando logs del contenedor (últimas 30 líneas):"
CONTAINER_ID=$(sudo docker ps -a --filter "name=notification" --format "{{.ID}}" | head -1)

if [ -n "$CONTAINER_ID" ]; then
  echo "Container ID: $CONTAINER_ID"
  sudo docker logs --tail 30 $CONTAINER_ID
  
  echo ""
  echo "Estado del contenedor:"
  sudo docker inspect $CONTAINER_ID --format '{{.State.Status}}: {{.State.Error}}'
else
  echo "❌ No se encontró contenedor de notificaciones"
fi

echo ""
echo "Verificando conectividad a MongoDB:"
MONGO_HOST=$(grep MONGO_HOST /etc/environment | cut -d'=' -f2 | tr -d '"' | tr -d "'")
echo "MongoDB Host: $MONGO_HOST"

if [ -n "$MONGO_HOST" ]; then
  nc -zv $MONGO_HOST 27017 2>&1 || echo "No se pudo conectar a MongoDB"
fi
ENDSSH

echo ""
echo "=========================================="
echo "  Opciones de corrección"
echo "=========================================="
echo ""
echo "Si el contenedor no está corriendo, ejecuta:"
echo "  bash scripts/restart_notifications.sh"
echo ""
echo "Para ver logs en tiempo real:"
echo "  ssh ubuntu@$NOTIF_IP 'sudo docker logs -f \$(sudo docker ps -aq --filter \"name=notification\")'"
