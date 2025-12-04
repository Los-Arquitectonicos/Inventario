#!/bin/bash
# Script para reiniciar el servicio de notificaciones
# Ejecutar desde AWS CloudShell

set -e

echo "=========================================="
echo "  Reiniciar Servicio de Notificaciones"
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
echo "Reiniciando contenedor de notificaciones..."

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@$NOTIF_IP << 'ENDSSH'
# Cargar variables de entorno
source /etc/environment

# Detener y eliminar contenedor existente
echo "Deteniendo contenedor existente..."
sudo docker stop notifications-service 2>/dev/null || true
sudo docker rm notifications-service 2>/dev/null || true

# Construir imagen
echo "Construyendo imagen Docker..."
cd /home/ubuntu/notifications
sudo docker build -t notifications-service:latest .

# Iniciar contenedor
echo "Iniciando nuevo contenedor..."
sudo docker run -d \
  --name notifications-service \
  --restart unless-stopped \
  -p 8000:8000 \
  -e MONGO_HOST="$MONGO_HOST" \
  -e MONGO_PORT="${MONGO_PORT:-27017}" \
  -e MONGO_DATABASE="${MONGO_DATABASE:-notifications_db}" \
  -e SECRET_KEY="$SECRET_KEY" \
  -e SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}" \
  -e SMTP_PORT="${SMTP_PORT:-587}" \
  -e SMTP_USER="${SMTP_USER}" \
  -e SMTP_PASSWORD="${SMTP_PASSWORD}" \
  notifications-service:latest

echo ""
echo "Esperando 5 segundos para que el servicio inicie..."
sleep 5

echo ""
echo "Estado del contenedor:"
sudo docker ps --filter "name=notifications-service"

echo ""
echo "Logs recientes:"
sudo docker logs --tail 20 notifications-service
ENDSSH

echo ""
echo "=========================================="
echo "  ✅ Reinicio Completado"
echo "=========================================="
echo ""
echo "Verifica el servicio con:"
echo "  curl -k https://3.238.225.18:8443/notifications/health"
echo ""
echo "O ejecuta el test:"
echo "  python3 test_notifications_service.py"
