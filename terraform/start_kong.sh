#!/bin/bash

# Script para verificar e inicializar Kong Gateway
# Ejecutar desde CloudShell

set -e

KONG_IP="44.200.78.101"

echo "========================================"
echo "  VERIFICACIÓN E INICIO DE KONG"
echo "========================================"
echo ""

echo "[INFO] Conectando a Kong Gateway (${KONG_IP})..."
echo ""

# Ejecutar comandos remotos en Kong
ssh -o StrictHostKeyChecking=no ubuntu@${KONG_IP} << 'ENDSSH'

echo "========================================="
echo "1. VERIFICANDO ESTADO DE KONG"
echo "========================================="

# Verificar si Kong está instalado
if command -v kong &> /dev/null; then
    echo "✅ Kong está instalado"
    kong version
else
    echo "❌ Kong NO está instalado"
    exit 1
fi

echo ""
echo "========================================="
echo "2. VERIFICANDO PROCESOS DE KONG"
echo "========================================="

# Verificar procesos Kong
KONG_PROCESSES=$(ps aux | grep -E "kong|nginx: master" | grep -v grep || echo "")
if [ -z "$KONG_PROCESSES" ]; then
    echo "⚠️  Kong NO está corriendo"
else
    echo "✅ Kong está corriendo:"
    echo "$KONG_PROCESSES"
fi

echo ""
echo "========================================="
echo "3. VERIFICANDO PUERTOS"
echo "========================================="

# Verificar puertos
sudo netstat -tulpn | grep -E ':(8000|8001)' || echo "⚠️  Kong no está escuchando en puertos 8000/8001"

echo ""
echo "========================================="
echo "4. VERIFICANDO ARCHIVOS DE CONFIGURACIÓN"
echo "========================================="

# Verificar archivos de configuración
if [ -f /etc/kong/kong.conf ]; then
    echo "✅ /etc/kong/kong.conf existe"
else
    echo "❌ /etc/kong/kong.conf NO existe"
fi

if [ -f /etc/kong/kong.yml ]; then
    echo "✅ /etc/kong/kong.yml existe"
    echo ""
    echo "Contenido de kong.yml:"
    cat /etc/kong/kong.yml
else
    echo "❌ /etc/kong/kong.yml NO existe"
fi

echo ""
echo "========================================="
echo "5. INICIANDO KONG SI NO ESTÁ CORRIENDO"
echo "========================================="

# Intentar iniciar Kong si no está corriendo
if [ -z "$KONG_PROCESSES" ]; then
    echo "[INFO] Intentando iniciar Kong..."
    
    # Verificar que existe la configuración
    if [ ! -f /etc/kong/kong.conf ]; then
        echo "[INFO] Creando configuración de Kong..."
        sudo mkdir -p /etc/kong /var/log/kong
        
        sudo tee /etc/kong/kong.conf > /dev/null <<'CONF'
database = off
declarative_config = /etc/kong/kong.yml
proxy_listen = 0.0.0.0:8000
admin_listen = 127.0.0.1:8001
log_level = info
CONF
        echo "✅ Configuración creada"
    fi
    
    # Verificar que existe el archivo de servicios
    if [ ! -f /etc/kong/kong.yml ]; then
        echo "[INFO] Creando configuración de servicios de Kong..."
        
        # Obtener IPs privadas de los backends
        DJANGO_IP="172.31.72.163"  # app_server_1
        NOTIFICATIONS_IP="172.31.71.201"  # Usar MongoDB IP temporalmente hasta obtener la correcta
        
        sudo tee /etc/kong/kong.yml > /dev/null <<YML
_format_version: "3.0"
services:
  - name: django-api
    url: http://${DJANGO_IP}:8000
    routes:
      - name: django-routes
        paths: ["/api", "/inventario", "/admin"]
  - name: notifications
    url: http://13.220.190.9:3001
    routes:
      - name: notification-routes
        paths: ["/notifications"]
YML
        echo "✅ Configuración de servicios creada"
    fi
    
    # Iniciar Kong
    echo "[INFO] Iniciando Kong..."
    sudo kong start -c /etc/kong/kong.conf
    
    # Esperar un momento
    sleep 3
    
    # Verificar que inició correctamente
    if ps aux | grep -E "kong|nginx: master" | grep -v grep > /dev/null; then
        echo "✅ Kong se inició correctamente"
    else
        echo "❌ Error al iniciar Kong"
        echo ""
        echo "Ver logs:"
        sudo tail -20 /var/log/kong/error.log
        exit 1
    fi
else
    echo "[INFO] Kong ya está corriendo, verificando salud..."
    sudo kong health || echo "⚠️  Kong health check falló"
fi

echo ""
echo "========================================="
echo "6. VERIFICACIÓN FINAL"
echo "========================================="

# Verificar que Kong responde
echo "[INFO] Probando Kong en localhost..."
curl -s http://localhost:8000/ > /dev/null 2>&1 && echo "✅ Kong responde en puerto 8000" || echo "❌ Kong NO responde en puerto 8000"

# Verificar admin API
echo "[INFO] Probando Kong Admin API..."
curl -s http://localhost:8001/ > /dev/null 2>&1 && echo "✅ Kong Admin API responde" || echo "❌ Kong Admin API NO responde"

# Listar servicios configurados
echo ""
echo "[INFO] Servicios configurados:"
curl -s http://localhost:8001/services 2>/dev/null | grep -o '"name":"[^"]*"' || echo "No se pudieron listar servicios"

# Listar rutas configuradas
echo ""
echo "[INFO] Rutas configuradas:"
curl -s http://localhost:8001/routes 2>/dev/null | grep -o '"paths":\[[^]]*\]' || echo "No se pudieron listar rutas"

echo ""
echo "========================================="
echo "7. LOGS RECIENTES"
echo "========================================="

if [ -f /var/log/kong/error.log ]; then
    echo "[INFO] Últimas 20 líneas de error.log:"
    sudo tail -20 /var/log/kong/error.log
else
    echo "⚠️  No hay logs de error disponibles"
fi

echo ""
echo "========================================"
echo "  VERIFICACIÓN COMPLETADA"
echo "========================================"
echo ""
echo "Estado de Kong:"
ps aux | grep -E "kong|nginx: master" | grep -v grep || echo "Kong NO está corriendo"
echo ""
echo "Puertos en escucha:"
sudo netstat -tulpn | grep -E ':(8000|8001)' || echo "No hay puertos Kong en escucha"

ENDSSH

echo ""
echo "========================================"
echo "  RESULTADO"
echo "========================================"
echo ""
echo "Para probar Kong desde tu máquina local:"
echo "  curl http://${KONG_IP}:8000/"
echo ""
echo "Para ver el estado del Target Group:"
echo "  Ve a AWS Console > EC2 > Load Balancers > Target Groups"
echo ""
