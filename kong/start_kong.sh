#!/bin/bash
# Script para iniciar/reiniciar Kong API Gateway en EC2
# Modo DB-less con configuración declarativa

set -e

echo "🦍 === Iniciando Kong API Gateway ==="
echo ""

# Directorios
KONG_CONFIG_DIR="/etc/kong"
KONG_LOG_DIR="/var/log/kong"
WORKSPACE_DIR="/home/ubuntu/app/Inventario"

# 1. Verificar si Kong está instalado
echo "1️⃣ Verificando instalación de Kong..."
if ! command -v kong &> /dev/null; then
    echo "   ❌ Kong no está instalado"
    echo "   💡 Instalar con: sudo apt install kong"
    exit 1
fi
echo "   ✅ Kong instalado: $(kong version 2>/dev/null | head -1)"
echo ""

# 2. Detener Kong si está corriendo
echo "2️⃣ Deteniendo Kong actual..."
sudo kong stop 2>/dev/null || echo "   ℹ️  Kong no estaba corriendo"
sleep 2
echo ""

# 3. Crear directorios necesarios
echo "3️⃣ Verificando directorios..."
sudo mkdir -p $KONG_CONFIG_DIR
sudo mkdir -p $KONG_LOG_DIR
sudo chown -R ubuntu:ubuntu $KONG_LOG_DIR
echo "   ✅ Directorios verificados"
echo ""

# 4. Copiar archivos de configuración
echo "4️⃣ Copiando archivos de configuración..."
if [ -f "$WORKSPACE_DIR/kong/kong.conf" ]; then
    sudo cp $WORKSPACE_DIR/kong/kong.conf $KONG_CONFIG_DIR/kong.conf
    echo "   ✅ kong.conf copiado"
else
    echo "   ⚠️  kong.conf no encontrado en workspace"
fi

if [ -f "$WORKSPACE_DIR/kong/kong.yml" ]; then
    sudo cp $WORKSPACE_DIR/kong/kong.yml $KONG_CONFIG_DIR/kong.yml
    echo "   ✅ kong.yml copiado"
else
    echo "   ⚠️  kong.yml no encontrado en workspace"
fi
echo ""

# 5. Validar configuración
echo "5️⃣ Validando configuración..."
if sudo kong check $KONG_CONFIG_DIR/kong.conf; then
    echo "   ✅ Configuración válida"
else
    echo "   ❌ Error en la configuración"
    exit 1
fi
echo ""

# 6. Obtener IPs de instancias Django
echo "6️⃣ Detectando instancias Django..."
DJANGO_IPS=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=django-instance-*" \
              "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].PrivateIpAddress' \
    --output text 2>/dev/null || echo "")

if [ -n "$DJANGO_IPS" ]; then
    echo "   ✅ Instancias Django encontradas:"
    for ip in $DJANGO_IPS; do
        echo "      - $ip:8080"
    done
else
    echo "   ⚠️  No se detectaron instancias Django automáticamente"
    echo "   ℹ️  Usando configuración estática de kong.yml"
fi
echo ""

# 7. Actualizar targets dinámicamente (opcional)
if [ -n "$DJANGO_IPS" ]; then
    echo "7️⃣ Actualizando targets en kong.yml..."
    # Backup del archivo original
    sudo cp $KONG_CONFIG_DIR/kong.yml $KONG_CONFIG_DIR/kong.yml.backup
    
    # TODO: Agregar lógica para actualizar targets dinámicamente
    echo "   ℹ️  Usando targets estáticos por ahora"
fi
echo ""

# 8. Iniciar Kong
echo "8️⃣ Iniciando Kong..."
if sudo kong start -c $KONG_CONFIG_DIR/kong.conf; then
    echo "   ✅ Kong iniciado exitosamente"
else
    echo "   ❌ Error al iniciar Kong"
    echo ""
    echo "📋 Últimas líneas del log de error:"
    sudo tail -20 $KONG_LOG_DIR/error.log
    exit 1
fi
echo ""

# 9. Esperar que Kong esté listo
echo "9️⃣ Esperando que Kong esté listo..."
sleep 5

# 10. Verificar estado
echo "🔟 Verificando estado..."
echo ""

# Verificar proceso
if pgrep -x nginx > /dev/null; then
    echo "   ✅ Proceso Kong/Nginx corriendo"
    ps aux | grep nginx | grep master | head -1
else
    echo "   ❌ Proceso Kong no encontrado"
    exit 1
fi

echo ""

# Verificar puertos
echo "   📡 Puertos en uso:"
if sudo lsof -i :8000 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "      ✅ Puerto 8000 (Proxy HTTP)"
else
    echo "      ❌ Puerto 8000 no accesible"
fi

if sudo lsof -i :8001 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "      ✅ Puerto 8001 (Admin API)"
else
    echo "      ⚠️  Puerto 8001 no accesible (solo localhost)"
fi

if sudo lsof -i :8100 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "      ✅ Puerto 8100 (Status/Health)"
else
    echo "      ❌ Puerto 8100 no accesible"
fi

echo ""

# Verificar health check
echo "   🏥 Health Check:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/status 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ Status endpoint responde: HTTP $HTTP_CODE"
else
    echo "      ⚠️  Status endpoint: HTTP $HTTP_CODE"
fi

echo ""

# Verificar servicios configurados
echo "   🔍 Servicios configurados:"
if curl -s http://localhost:8001/services 2>/dev/null | grep -q "django-api"; then
    echo "      ✅ Servicio django-api detectado"
else
    echo "      ⚠️  No se detectaron servicios"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Kong Gateway iniciado correctamente"
echo ""
echo "📊 URLs de acceso:"
echo "   - Proxy HTTP:  http://$(curl -s ifconfig.me):8000"
echo "   - Status:      http://$(curl -s ifconfig.me):8100/status"
echo "   - Admin API:   http://localhost:8001 (solo local)"
echo ""
echo "💡 Comandos útiles:"
echo "   - Ver logs:         sudo tail -f $KONG_LOG_DIR/access.log"
echo "   - Detener Kong:     sudo kong stop"
echo "   - Recargar config:  sudo kong reload"
echo "   - Health check:     curl http://localhost:8100/status"
echo ""
echo "🔗 Probar aplicación:"
echo "   curl http://localhost:8000/inventario/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
