#!/bin/bash
# Script para actualizar la configuración de Kong usando AWS Systems Manager

set -e

REGION="us-east-1"
KONG_INSTANCE_NAME="provesi-kong-instance"
ALB_DNS="provesi-alb-272371447.us-east-1.elb.amazonaws.com"
NOTIFICATIONS_IP="172.31.67.162"

echo "=== Actualizando configuración de Kong ==="

# 1. Obtener el Instance ID de Kong
echo "1. Buscando instancia de Kong..."
INSTANCE_ID=$(aws ec2 describe-instances \
  --region $REGION \
  --filters "Name=tag:Name,Values=$KONG_INSTANCE_NAME" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
  echo "❌ Error: No se encontró la instancia de Kong"
  exit 1
fi

echo "✅ Instancia Kong encontrada: $INSTANCE_ID"

# 2. Ejecutar comandos en la instancia usando SSM
echo "2. Actualizando kong.yaml en el servidor..."

COMMANDS=$(cat << 'EOF'
cd /opt/kong/Inventario
sudo git pull origin servicediscovery
sudo sed -i "s|<DJANGO_HOST>|provesi-alb-272371447.us-east-1.elb.amazonaws.com|g" kong.yaml
sudo sed -i "s|<NOTIFICATIONS_HOST>|172.31.67.162|g" kong.yaml
echo "=== Kong YAML actualizado ==="
cat kong.yaml
echo ""
echo "=== Reiniciando Kong ==="
sudo docker restart kong
sleep 5
echo "=== Logs de Kong ==="
sudo docker logs kong --tail 30
EOF
)

COMMAND_ID=$(aws ssm send-command \
  --region $REGION \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=[\"$COMMANDS\"]" \
  --query "Command.CommandId" \
  --output text)

if [ -z "$COMMAND_ID" ]; then
  echo "❌ Error: No se pudo enviar el comando"
  exit 1
fi

echo "✅ Comando enviado: $COMMAND_ID"
echo "3. Esperando resultado (30 segundos)..."
sleep 30

# 3. Obtener el output del comando
echo "4. Obteniendo resultado..."
aws ssm get-command-invocation \
  --region $REGION \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query "StandardOutputContent" \
  --output text

echo ""
echo "=== Configuración completada ==="
echo "Prueba Kong:"
echo "  curl http://3.238.225.18:8000/inventario/"
