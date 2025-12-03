#!/bin/bash
# Script para agregar regla de puerto 8443 al security group de Kong
# Ejecutar desde AWS CloudShell o máquina con AWS CLI configurado

set -e

REGION="us-east-1"
SG_NAME="provesi-traffic-kong"

echo "=== Agregando puerto 8443 al Security Group de Kong ==="

# 1. Buscar el Security Group
echo "1. Buscando Security Group '$SG_NAME'..."
SG_ID=$(aws ec2 describe-security-groups \
  --region $REGION \
  --filters "Name=group-name,Values=$SG_NAME" \
  --query "SecurityGroups[0].GroupId" \
  --output text)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
  echo "❌ Error: No se encontró el Security Group '$SG_NAME'"
  exit 1
fi

echo "✅ Security Group encontrado: $SG_ID"

# 2. Verificar si la regla ya existe
echo "2. Verificando reglas existentes..."
EXISTING_RULE=$(aws ec2 describe-security-groups \
  --region $REGION \
  --group-ids $SG_ID \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`8443\`]" \
  --output text)

if [ ! -z "$EXISTING_RULE" ]; then
  echo "⚠️  La regla para puerto 8443 ya existe"
  echo "Regla existente:"
  aws ec2 describe-security-groups \
    --region $REGION \
    --group-ids $SG_ID \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`8443\`]"
  exit 0
fi

# 3. Agregar regla para puerto 8443
echo "3. Agregando regla para puerto 8443 (HTTPS)..."
aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8443 \
  --cidr 0.0.0.0/0 \
  --group-description "Kong HTTPS access"

echo "✅ Regla agregada exitosamente"

# 4. Verificar la nueva configuración
echo "4. Verificando configuración final..."
aws ec2 describe-security-groups \
  --region $REGION \
  --group-ids $SG_ID \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`8443\` || FromPort==\`8000\`]"

echo ""
echo "=== Configuración completada ==="
echo "Security Group ID: $SG_ID"
echo "Puertos abiertos: 8000 (HTTP), 8443 (HTTPS)"
echo ""
echo "Prueba la conexión:"
echo "  curl -k https://3.238.225.18:8443/inventario/"
