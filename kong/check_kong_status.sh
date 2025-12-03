#!/bin/bash
# Script para verificar el estado de Kong API Gateway

echo "🔍 === Estado de Kong API Gateway ==="
echo ""

# 1. Verificar proceso
echo "1️⃣ Proceso Kong/Nginx:"
if pgrep -x nginx > /dev/null; then
    echo "   ✅ Kong está corriendo"
    ps aux | grep nginx | grep -E "master|worker" | head -3
else
    echo "   ❌ Kong NO está corriendo"
    echo "   💡 Iniciar con: bash /home/ubuntu/app/Inventario/kong/start_kong.sh"
    exit 1
fi

echo ""

# 2. Verificar puertos
echo "2️⃣ Puertos:"
for PORT in 8000 8001 8100; do
    if sudo lsof -i :$PORT -sTCP:LISTEN > /dev/null 2>&1; then
        case $PORT in
            8000) DESC="Proxy HTTP" ;;
            8001) DESC="Admin API" ;;
            8100) DESC="Status/Health" ;;
        esac
        echo "   ✅ Puerto $PORT ($DESC)"
    else
        echo "   ❌ Puerto $PORT no accesible"
    fi
done

echo ""

# 3. Health check
echo "3️⃣ Health Check:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/status 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Status endpoint: HTTP $HTTP_CODE"
    curl -s http://localhost:8100/status | python3 -m json.tool 2>/dev/null | head -20
else
    echo "   ❌ Status endpoint: HTTP $HTTP_CODE"
fi

echo ""

# 4. Servicios configurados
echo "4️⃣ Servicios configurados:"
SERVICES=$(curl -s http://localhost:8001/services 2>/dev/null)
if echo "$SERVICES" | grep -q "django-api"; then
    echo "   ✅ django-api"
    echo "$SERVICES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for svc in data.get('data', []):
    print(f\"      - {svc['name']}: {svc['url']}\")
" 2>/dev/null || echo "      (formato inesperado)"
else
    echo "   ⚠️  No se detectaron servicios"
fi

echo ""

# 5. Rutas configuradas
echo "5️⃣ Rutas configuradas:"
ROUTES=$(curl -s http://localhost:8001/routes 2>/dev/null)
if echo "$ROUTES" | grep -q "data"; then
    ROUTE_COUNT=$(echo "$ROUTES" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', [])))" 2>/dev/null || echo "?")
    echo "   ✅ $ROUTE_COUNT ruta(s) configurada(s)"
else
    echo "   ⚠️  No se pudieron obtener rutas"
fi

echo ""

# 6. Logs recientes
echo "6️⃣ Últimas líneas del log de acceso:"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f /var/log/kong/access.log ]; then
    sudo tail -5 /var/log/kong/access.log | sed 's/^/   /'
else
    echo "   ⚠️  No se encontró /var/log/kong/access.log"
fi

echo ""

# 7. Errores recientes
echo "7️⃣ Errores recientes (últimas 5 líneas):"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f /var/log/kong/error.log ]; then
    ERROR_LINES=$(sudo tail -5 /var/log/kong/error.log)
    if [ -n "$ERROR_LINES" ]; then
        echo "$ERROR_LINES" | sed 's/^/   /'
    else
        echo "   ✅ Sin errores recientes"
    fi
else
    echo "   ⚠️  No se encontró /var/log/kong/error.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Comandos útiles:"
echo "   - Reiniciar Kong:     bash /home/ubuntu/app/Inventario/kong/restart_kong.sh"
echo "   - Ver logs en vivo:   sudo tail -f /var/log/kong/access.log"
echo "   - Recargar config:    sudo kong reload"
echo "   - Detener Kong:       sudo kong stop"
echo ""
echo "🔗 Probar endpoints:"
echo "   curl http://localhost:8000/inventario/"
echo "   curl http://localhost:8100/status"
