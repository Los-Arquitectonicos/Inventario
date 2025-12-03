#!/bin/bash

# Script de diagnóstico de infraestructura
# Ejecutar desde CloudShell donde tienes acceso SSH

set -e

echo "========================================"
echo "  DIAGNÓSTICO DE INFRAESTRUCTURA"
echo "========================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# IPs desde los outputs de Terraform
KONG_IP="44.200.78.101"
NOTIFICATIONS_IP="13.220.190.9"
APP_SERVER_1="98.82.139.233"
APP_SERVER_2="3.239.49.135"

echo "================================================"
echo "1. VERIFICANDO KONG GATEWAY"
echo "================================================"

echo -e "\n${YELLOW}[INFO]${NC} Conectando a Kong Gateway..."
ssh -o StrictHostKeyChecking=no ubuntu@${KONG_IP} << 'EOF'
echo "=== Estado del servicio Kong ==="
sudo systemctl status kong || echo "Kong no está instalado como servicio systemd"

echo -e "\n=== Procesos Kong ==="
ps aux | grep kong | grep -v grep || echo "No hay procesos Kong corriendo"

echo -e "\n=== Contenedores Docker Kong ==="
docker ps | grep kong || echo "No hay contenedores Kong corriendo"

echo -e "\n=== Puertos en escucha ==="
sudo netstat -tulpn | grep -E ':(8000|8001|8443|8444)' || echo "Kong no está escuchando en puertos esperados"

echo -e "\n=== Logs recientes de Kong ==="
sudo journalctl -u kong -n 50 --no-pager || echo "No hay logs de systemd"
EOF

echo ""
echo "================================================"
echo "2. VERIFICANDO SERVICIO DE NOTIFICACIONES"
echo "================================================"

echo -e "\n${YELLOW}[INFO]${NC} Conectando a servidor de Notificaciones..."
ssh -o StrictHostKeyChecking=no ubuntu@${NOTIFICATIONS_IP} << 'EOF'
echo "=== Procesos Node.js ==="
ps aux | grep node | grep -v grep || echo "No hay procesos Node.js corriendo"

echo -e "\n=== Puertos en escucha ==="
sudo netstat -tulpn | grep -E ':300[0-9]' || echo "Servicio de notificaciones no está escuchando"

echo -e "\n=== Archivos del proyecto ==="
ls -la /home/ubuntu/notifications/ || echo "Directorio de notificaciones no existe"

echo -e "\n=== Contenido del archivo .env ==="
cat /home/ubuntu/notifications/.env 2>/dev/null || echo "Archivo .env no existe"

echo -e "\n=== Logs de PM2 si existe ==="
pm2 list || echo "PM2 no está instalado"
EOF

echo ""
echo "================================================"
echo "3. VERIFICANDO SERVIDORES DJANGO"
echo "================================================"

for i in 1 2; do
    if [ $i -eq 1 ]; then
        APP_IP=$APP_SERVER_1
    else
        APP_IP=$APP_SERVER_2
    fi
    
    echo -e "\n${YELLOW}[INFO]${NC} Conectando a App Server $i (${APP_IP})..."
    ssh -o StrictHostKeyChecking=no ubuntu@${APP_IP} << 'EOF'
echo "=== Procesos Gunicorn/Django ==="
ps aux | grep gunicorn | grep -v grep || echo "No hay procesos Gunicorn corriendo"

echo -e "\n=== Puertos en escucha ==="
sudo netstat -tulpn | grep -E ':(8000|8080)' || echo "Django no está escuchando en puertos esperados"

echo -e "\n=== Archivos del proyecto ==="
ls -la /home/ubuntu/ProvesiWMS/ || echo "Directorio del proyecto no existe"
EOF
done

echo ""
echo "========================================"
echo "  DIAGNÓSTICO COMPLETADO"
echo "========================================"
echo ""
echo "Próximos pasos basados en los resultados:"
echo "1. Si Kong no está corriendo → Iniciar Kong"
echo "2. Si Notificaciones no está corriendo → Iniciar servicio Node.js"
echo "3. Si Django no está corriendo → Iniciar Gunicorn"
echo "4. Verificar grupos de seguridad en AWS Console"
