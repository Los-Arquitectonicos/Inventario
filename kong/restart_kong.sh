#!/bin/bash
# Script simple para reiniciar Kong (sin detección automática de instancias)

set -e

echo "🔄 === Reiniciando Kong API Gateway ==="
echo ""

# 1. Detener Kong
echo "1️⃣ Deteniendo Kong..."
sudo kong stop 2>/dev/null || echo "   ℹ️  Kong no estaba corriendo"
sleep 2

# 2. Verificar archivos de configuración
echo "2️⃣ Verificando configuración..."
if [ ! -f "/etc/kong/kong.conf" ]; then
    echo "   ❌ /etc/kong/kong.conf no encontrado"
    exit 1
fi

if [ ! -f "/etc/kong/kong.yml" ]; then
    echo "   ❌ /etc/kong/kong.yml no encontrado"
    exit 1
fi

echo "   ✅ Archivos de configuración presentes"

# 3. Validar configuración
echo "3️⃣ Validando configuración..."
if sudo kong check /etc/kong/kong.conf; then
    echo "   ✅ Configuración válida"
else
    echo "   ❌ Error en la configuración"
    exit 1
fi

# 4. Iniciar Kong
echo "4️⃣ Iniciando Kong..."
if sudo kong start -c /etc/kong/kong.conf; then
    echo "   ✅ Kong iniciado"
else
    echo "   ❌ Error al iniciar Kong"
    sudo tail -20 /var/log/kong/error.log
    exit 1
fi

# 5. Verificar
sleep 3
echo "5️⃣ Verificando estado..."

if pgrep -x nginx > /dev/null; then
    echo "   ✅ Kong corriendo"
else
    echo "   ❌ Kong no está corriendo"
    exit 1
fi

# Health check
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/status 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Health check: HTTP $HTTP_CODE"
else
    echo "   ⚠️  Health check: HTTP $HTTP_CODE"
fi

echo ""
echo "✅ Kong reiniciado correctamente"
echo "💡 Ver logs: sudo tail -f /var/log/kong/access.log"
