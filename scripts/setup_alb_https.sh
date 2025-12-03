#!/bin/bash
# Script para configurar HTTPS en el ALB sin usar Terraform
# Ejecutar desde AWS CloudShell o máquina con AWS CLI configurado

set -e

# Variables
REGION="us-east-1"
ALB_NAME="provesi-alb"
CERT_NAME="provesi-alb-cert"

echo "=== Configurando HTTPS en ALB ==="

# 1. Obtener el ARN del ALB
echo "1. Buscando ALB..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --region $REGION \
  --query "LoadBalancers[?LoadBalancerName=='$ALB_NAME'].LoadBalancerArn" \
  --output text)

if [ -z "$ALB_ARN" ]; then
  echo "❌ Error: No se encontró el ALB '$ALB_NAME'"
  exit 1
fi
echo "✅ ALB encontrado: $ALB_ARN"

# 2. Obtener el listener HTTP existente
echo "2. Buscando listener HTTP..."
HTTP_LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --region $REGION \
  --query "Listeners[?Port==\`80\`].ListenerArn" \
  --output text)

if [ -z "$HTTP_LISTENER_ARN" ]; then
  echo "❌ Error: No se encontró el listener HTTP"
  exit 1
fi
echo "✅ Listener HTTP encontrado: $HTTP_LISTENER_ARN"

# 3. Obtener el Target Group ARN
echo "3. Obteniendo Target Group..."
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
  --region $REGION \
  --query "TargetGroups[?contains(TargetGroupName, 'provesi-django')].TargetGroupArn" \
  --output text | head -1)

if [ -z "$TARGET_GROUP_ARN" ]; then
  echo "❌ Error: No se encontró el Target Group"
  exit 1
fi
echo "✅ Target Group encontrado: $TARGET_GROUP_ARN"

# 4. Generar certificado self-signed
echo "4. Generando certificado SSL self-signed..."
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --region $REGION \
  --query "LoadBalancers[?LoadBalancerName=='$ALB_NAME'].DNSName" \
  --output text)

# Crear certificado temporal
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout /tmp/alb-private-key.pem \
  -out /tmp/alb-certificate.pem \
  -days 365 \
  -subj "/CN=$ALB_DNS/O=Provesi WMS"

echo "✅ Certificado generado"

# 5. Importar certificado a ACM
echo "5. Importando certificado a ACM..."
CERT_ARN=$(aws acm import-certificate \
  --certificate fileb:///tmp/alb-certificate.pem \
  --private-key fileb:///tmp/alb-private-key.pem \
  --region $REGION \
  --tags Key=Name,Value=$CERT_NAME Key=Project,Value=provesi-wms \
  --query CertificateArn \
  --output text)

if [ -z "$CERT_ARN" ]; then
  echo "❌ Error: No se pudo importar el certificado"
  exit 1
fi
echo "✅ Certificado importado: $CERT_ARN"

# Limpiar archivos temporales
rm -f /tmp/alb-private-key.pem /tmp/alb-certificate.pem

# 6. Crear listener HTTPS
echo "6. Creando listener HTTPS en puerto 443..."
HTTPS_LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --ssl-policy ELBSecurityPolicy-2016-08 \
  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
  --region $REGION \
  --query 'Listeners[0].ListenerArn' \
  --output text)

if [ -z "$HTTPS_LISTENER_ARN" ]; then
  echo "❌ Error: No se pudo crear el listener HTTPS"
  exit 1
fi
echo "✅ Listener HTTPS creado: $HTTPS_LISTENER_ARN"

# 7. Modificar listener HTTP para redirigir a HTTPS
echo "7. Configurando redirección HTTP -> HTTPS..."
aws elbv2 modify-listener \
  --listener-arn $HTTP_LISTENER_ARN \
  --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
  --region $REGION \
  --output text > /dev/null

echo "✅ Redirección HTTP->HTTPS configurada"

# 8. Verificar configuración
echo ""
echo "=== Configuración completada ==="
echo "ALB DNS: $ALB_DNS"
echo "Certificado ARN: $CERT_ARN"
echo "Listener HTTPS ARN: $HTTPS_LISTENER_ARN"
echo ""
echo "Prueba la configuración:"
echo "  curl -k https://$ALB_DNS/inventario/"
echo ""
echo "⚠️  Nota: El certificado es self-signed, usa -k con curl o acepta la advertencia en el navegador"
