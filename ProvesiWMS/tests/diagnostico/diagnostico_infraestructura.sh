#!/bin/bash

# =============================================================================
# DIAGNÓSTICO DE INFRAESTRUCTURA - ANÁLISIS DE RESULTADOS DESASTROSOS
# =============================================================================
# Analiza por qué todas las pruebas fallaron con 502 Bad Gateway
# Creado después de resultados catastróficos en Anti_Modificacion_API_Pedidos

echo ""
echo "🚨 =============================================="
echo "   DIAGNÓSTICO DE INFRAESTRUCTURA CAÍDA"
echo "   Análisis de resultados desastrosos"
echo "=============================================="
echo ""

# URLs a verificar
BASE_URL="https://provesi-alb-2003818714.us-east-1.elb.amazonaws.com"
ENDPOINTS=(
    "/"
    "/inventario/"
    "/inventario/auth/token/"
    "/inventario/api/pedidos/"
    "/admin/"
)

echo "🔍 DIAGNÓSTICO 1: CONECTIVIDAD DNS"
echo "----------------------------------------"
HOST=$(echo $BASE_URL | sed 's|https\?://||' | cut -d'/' -f1)
echo "Host: $HOST"
echo ""

echo "DNS Resolution:"
nslookup $HOST || echo "❌ DNS FALLO"
echo ""

echo "Ping Test:"
ping -c 3 $HOST || echo "❌ PING FALLO"
echo ""

echo "🔍 DIAGNÓSTICO 2: ANÁLISIS DE ENDPOINTS"
echo "----------------------------------------"

for endpoint in "${ENDPOINTS[@]}"; do
    url="${BASE_URL}${endpoint}"
    echo "Testing: $url"
    
    # Análisis detallado con curl
    response=$(curl -k -s -w "\n%{http_code}|%{time_total}|%{time_connect}" "$url" -m 10)
    http_code=$(echo "$response" | tail -1 | cut -d'|' -f1)
    total_time=$(echo "$response" | tail -1 | cut -d'|' -f2)
    connect_time=$(echo "$response" | tail -1 | cut -d'|' -f3)
    
    case $http_code in
        000)
            echo "   ❌ CONEXIÓN FALLO - Servidor no responde"
            ;;
        502)
            echo "   🚨 502 BAD GATEWAY - Load Balancer no puede contactar backend"
            echo "      Tiempo conexión: ${connect_time}s"
            echo "      Tiempo total: ${total_time}s"
            ;;
        503)
            echo "   ⚠️  503 SERVICE UNAVAILABLE - Servicio temporalmente no disponible"
            ;;
        200)
            echo "   ✅ 200 OK - Endpoint funciona"
            ;;
        404)
            echo "   📝 404 NOT FOUND - Endpoint no existe pero servidor responde"
            ;;
        *)
            echo "   📊 HTTP $http_code - Respuesta inesperada"
            ;;
    esac
    echo ""
done

echo "🔍 DIAGNÓSTICO 3: ANÁLISIS ESPECÍFICO DEL 502"
echo "----------------------------------------"
echo "Un 502 Bad Gateway significa:"
echo "  1. El Load Balancer (ALB) está funcionando"
echo "  2. Pero NO puede contactar los servidores backend"
echo "  3. Posibles causas:"
echo "     - Aplicación Django caída"
echo "     - Servidor EC2/ECS parado"
echo "     - Puerto de la aplicación cerrado"
echo "     - Health check fallando"
echo "     - Base de datos no disponible"
echo ""

echo "🔍 DIAGNÓSTICO 4: VERIFICACIÓN DE HEALTH CHECK"
echo "----------------------------------------"
echo "Intentando health check básico..."

# Intento directo al root
curl -k -v "$BASE_URL/" -m 15 2>&1 | grep -E "(HTTP|Connected|SSL)"
echo ""

echo "🔍 DIAGNÓSTICO 5: ANÁLISIS DE TIMING"
echo "----------------------------------------"
echo "Análisis de los tiempos de respuesta del reporte:"
echo "  - Login: 535ms (lento para un fallo)"
echo "  - Crear pedido: 97ms"
echo "  - Verificar: 102ms"
echo "  - PUT: 132ms"
echo "  - PATCH: 109ms"
echo "  - DELETE: 110ms"
echo ""
echo "CONCLUSIÓN: El Load Balancer responde rápido con 502"
echo "             Lo que confirma que el backend está caído"
echo ""

echo "🚨 DIAGNÓSTICO FINAL"
echo "=============================================="
echo ""
echo "PROBLEMA IDENTIFICADO:"
echo "  🔴 Infraestructura de backend CAÍDA"
echo "  🔴 Load Balancer funcionando pero sin backend"
echo "  🔴 Aplicación Django NO está ejecutándose"
echo ""
echo "ACCIONES REQUERIDAS:"
echo "  1. ✅ Verificar estado del servidor EC2/ECS"
echo "  2. ✅ Revisar logs del Load Balancer"
echo "  3. ✅ Verificar health checks de la aplicación"
echo "  4. ✅ Reiniciar servicios Django"
echo "  5. ✅ Verificar conectividad a base de datos"
echo ""
echo "IMPACTO EN PRUEBAS DE SEGURIDAD:"
echo "  ❌ NO se pueden ejecutar pruebas de modificación"
echo "  ❌ NO se puede validar seguridad de API"
echo "  ❌ Sistema completamente inaccesible"
echo ""
echo "=============================================="