#!/bin/bash

# Script para verificar e inicializar Notifications Service
# Ejecutar desde CloudShell

set -e

NOTIFICATIONS_IP="13.220.190.9"
MONGODB_IP="172.31.71.201"

echo "========================================"
echo "  VERIFICACIÓN E INICIO DE NOTIFICATIONS"
echo "========================================"
echo ""

echo "[INFO] Conectando a Notifications Server (${NOTIFICATIONS_IP})..."
echo ""

# Ejecutar comandos remotos en Notifications
ssh -o StrictHostKeyChecking=no ubuntu@${NOTIFICATIONS_IP} << 'ENDSSH'

echo "========================================="
echo "1. VERIFICANDO NODE.JS Y NPM"
echo "========================================="

# Verificar Node.js
if command -v node &> /dev/null; then
    echo "✅ Node.js instalado: $(node --version)"
else
    echo "❌ Node.js NO está instalado"
    exit 1
fi

# Verificar NPM
if command -v npm &> /dev/null; then
    echo "✅ NPM instalado: $(npm --version)"
else
    echo "❌ NPM NO está instalado"
    exit 1
fi

# Verificar PM2
if command -v pm2 &> /dev/null; then
    echo "✅ PM2 instalado: $(pm2 --version)"
else
    echo "⚠️  PM2 NO está instalado, instalando..."
    sudo npm install -g pm2
fi

echo ""
echo "========================================="
echo "2. VERIFICANDO PROCESOS"
echo "========================================="

# Listar procesos PM2
echo "[INFO] Procesos PM2:"
pm2 list

# Verificar procesos Node.js
echo ""
echo "[INFO] Procesos Node.js:"
ps aux | grep node | grep -v grep || echo "No hay procesos Node.js corriendo"

echo ""
echo "========================================="
echo "3. VERIFICANDO PUERTOS"
echo "========================================="

sudo netstat -tulpn | grep 3001 || echo "⚠️  Puerto 3001 no está en escucha"

echo ""
echo "========================================="
echo "4. VERIFICANDO ARCHIVOS DEL PROYECTO"
echo "========================================="

# Verificar directorio del proyecto
if [ -d /home/ubuntu/Inventario/notifications ]; then
    echo "✅ Directorio del proyecto existe"
    echo ""
    echo "Contenido:"
    ls -la /home/ubuntu/Inventario/notifications/
else
    echo "❌ Directorio del proyecto NO existe"
    echo "[INFO] Clonando repositorio..."
    cd /home/ubuntu
    git clone https://github.com/Los-Arquitectonicos/Inventario.git
    cd Inventario
    git fetch origin notificaciones
    git checkout notificaciones
fi

# Verificar archivo .env
echo ""
if [ -f /home/ubuntu/Inventario/notifications/.env ]; then
    echo "✅ Archivo .env existe"
    echo ""
    echo "Contenido:"
    cat /home/ubuntu/Inventario/notifications/.env
else
    echo "⚠️  Archivo .env NO existe, creando..."
    cd /home/ubuntu/Inventario/notifications
    cat > .env << 'EOF'
PORT=3001
HOST=0.0.0.0
MONGO_URI=mongodb://172.31.71.201:27017/provesi_notifications
JWT_SECRET=django-insecure-test-key-2024
EOF
    echo "✅ Archivo .env creado"
fi

# Verificar server.js
echo ""
if [ -f /home/ubuntu/Inventario/notifications/server.js ]; then
    echo "✅ server.js existe"
else
    echo "❌ server.js NO existe"
    exit 1
fi

echo ""
echo "========================================="
echo "5. VERIFICANDO DEPENDENCIAS"
echo "========================================="

cd /home/ubuntu/Inventario/notifications

if [ -d node_modules ]; then
    echo "✅ node_modules existe"
else
    echo "⚠️  node_modules NO existe, instalando dependencias..."
    npm install
fi

echo ""
echo "========================================="
echo "6. INICIANDO SERVICIO SI NO ESTÁ CORRIENDO"
echo "========================================="

# Verificar si el servicio ya está corriendo
if pm2 list | grep -q "notifications"; then
    echo "[INFO] Servicio 'notifications' encontrado en PM2"
    
    # Verificar estado
    if pm2 list | grep notifications | grep -q "online"; then
        echo "✅ Servicio ya está corriendo"
        echo "[INFO] Reiniciando para aplicar cambios..."
        pm2 restart notifications
    else
        echo "⚠️  Servicio existe pero no está online, reiniciando..."
        pm2 restart notifications
    fi
else
    echo "[INFO] Servicio NO está en PM2, iniciando..."
    cd /home/ubuntu/Inventario/notifications
    pm2 start server.js --name notifications
    
    # Guardar configuración de PM2
    pm2 save
    
    # Configurar inicio automático
    sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
fi

# Esperar un momento
sleep 2

echo ""
echo "========================================="
echo "7. VERIFICACIÓN FINAL"
echo "========================================="

# Ver estado de PM2
echo "[INFO] Estado de PM2:"
pm2 list

# Ver logs recientes
echo ""
echo "[INFO] Logs recientes (últimas 30 líneas):"
pm2 logs notifications --lines 30 --nostream

# Probar endpoints
echo ""
echo "[INFO] Probando endpoints..."

curl -s http://localhost:3001/health && echo "✅ /health responde correctamente" || echo "❌ /health NO responde"
curl -s http://localhost:3001/ && echo "✅ / responde correctamente" || echo "❌ / NO responde"
curl -s http://localhost:3001/test && echo "✅ /test responde correctamente" || echo "❌ /test NO responde"

echo ""
echo "========================================="
echo "8. INFORMACIÓN DE MONITOREO"
echo "========================================="

echo "[INFO] Para ver logs en tiempo real:"
echo "  pm2 logs notifications"
echo ""
echo "[INFO] Para ver información detallada:"
echo "  pm2 show notifications"
echo ""
echo "[INFO] Para reiniciar el servicio:"
echo "  pm2 restart notifications"

echo ""
echo "========================================"
echo "  VERIFICACIÓN COMPLETADA"
echo "========================================"

ENDSSH

echo ""
echo "========================================"
echo "  RESULTADO"
echo "========================================"
echo ""
echo "Para probar Notifications desde tu máquina local:"
echo "  curl http://${NOTIFICATIONS_IP}:3001/health"
echo ""
echo "Para probar a través del ALB:"
echo "  curl -k https://provesi-alb-286933149.us-east-1.elb.amazonaws.com/notifications/health"
echo ""
