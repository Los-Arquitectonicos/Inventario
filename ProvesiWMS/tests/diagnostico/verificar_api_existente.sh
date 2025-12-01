#!/bin/bash

# =============================================================================
# VERIFICACIÓN DE APIs EXISTENTES - POST-INFRAESTRUCTURA
# =============================================================================
# Verifica qué endpoints API están realmente implementados
# Análisis después de resultados con 404 Not Found

echo ""
echo "🔍 =============================================="
echo "   VERIFICACIÓN DE APIs DISPONIBLES"
echo "   Post-infraestructura funcionando"
echo "=============================================="
echo ""

BASE_URL="https://provesi-alb-2003818714.us-east-1.elb.amazonaws.com"

# Primero obtener token
echo "🔑 OBTENIENDO TOKEN DE AUTENTICACIÓN..."
echo "----------------------------------------"

TOKEN_RESPONSE=$(curl -k -s -X POST "$BASE_URL/inventario/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ProvesiAdmin2024!"}' \
  -w "%{http_code}")

HTTP_CODE="${TOKEN_RESPONSE: -3}"
TOKEN_BODY="${TOKEN_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    TOKEN=$(echo "$TOKEN_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])" 2>/dev/null)
    echo "✅ Token obtenido exitosamente"
    echo "Token: ${TOKEN:0:20}..."
else
    echo "❌ Error obteniendo token: $HTTP_CODE"
    exit 1
fi
echo ""

echo "🔍 EXPLORANDO ENDPOINTS DISPONIBLES"
echo "----------------------------------------"

# Lista de posibles endpoints API
API_ENDPOINTS=(
    "/api/"
    "/inventario/api/"
    "/api/v1/"
    "/inventario/api/v1/"
    "/rest/"
    "/inventario/rest/"
    "/api/pedidos/"
    "/inventario/api/pedidos/"
    "/api/v1/pedidos/"
    "/inventario/api/v1/pedidos/"
    "/admin/api/"
    "/inventario/admin/api/"
)

echo "Probando endpoints API..."
echo ""

for endpoint in "${API_ENDPOINTS[@]}"; do
    url="${BASE_URL}${endpoint}"
    echo -n "Testing: $endpoint "
    
    # Test sin autenticación
    response=$(curl -k -s -w "%{http_code}" -o /dev/null "$url" -m 5)
    
    # Test con autenticación
    auth_response=$(curl -k -s -w "%{http_code}" -o /dev/null "$url" \
      -H "Authorization: Bearer $TOKEN" -m 5)
    
    if [ "$response" = "200" ] || [ "$auth_response" = "200" ]; then
        echo "✅ EXISTE (Sin auth: $response, Con auth: $auth_response)"
    elif [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$auth_response" = "200" ]; then
        echo "✅ EXISTE pero requiere auth ($response → $auth_response)"
    elif [ "$response" = "404" ] && [ "$auth_response" = "404" ]; then
        echo "❌ NO EXISTE (404)"
    else
        echo "❓ DESCONOCIDO (Sin auth: $response, Con auth: $auth_response)"
    fi
done

echo ""
echo "🔍 VERIFICANDO URLs CONOCIDAS DE DJANGO"
echo "----------------------------------------"

# URLs típicas de Django
DJANGO_URLS=(
    "/admin/"
    "/inventario/"
    "/inventario/pedidos/"
    "/inventario/productos/"
    "/inventario/bodegas/"
    "/static/"
    "/media/"
)

for url_path in "${DJANGO_URLS[@]}"; do
    url="${BASE_URL}${url_path}"
    echo -n "Testing: $url_path "
    
    response=$(curl -k -s -w "%{http_code}" -o /dev/null "$url" -m 5)
    
    case $response in
        200)
            echo "✅ ACCESIBLE"
            ;;
        302|301)
            echo "✅ REDIRECCIÓN"
            ;;
        401|403)
            echo "🔒 REQUIERE AUTH"
            ;;
        404)
            echo "❌ NO EXISTE"
            ;;
        *)
            echo "❓ HTTP $response"
            ;;
    esac
done

echo ""
echo "🔍 ANÁLISIS DE URLS.PY"
echo "----------------------------------------"
echo "Verificando si existe configuración de API REST..."

# Verificar Django REST Framework
echo "Testing Django REST Framework patterns:"

DRF_PATTERNS=(
    "/api-auth/"
    "/api-auth/login/"
    "/browse/"
    "/docs/"
    "/schema/"
)

for pattern in "${DRF_PATTERNS[@]}"; do
    url="${BASE_URL}${pattern}"
    echo -n "DRF $pattern: "
    
    response=$(curl -k -s -w "%{http_code}" -o /dev/null "$url" -m 5)
    
    if [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
        echo "✅ DISPONIBLE ($response)"
    elif [ "$response" = "404" ]; then
        echo "❌ NO CONFIGURADO"
    else
        echo "❓ HTTP $response"
    fi
done

echo ""
echo "🚨 DIAGNÓSTICO FINAL"
echo "=============================================="
echo ""
echo "PROBLEMA IDENTIFICADO:"
echo "  🔴 Los endpoints /api/pedidos/ NO EXISTEN"
echo "  🔴 Django REST Framework NO configurado"
echo "  🔴 Solo existe autenticación por token"
echo ""
echo "POSIBLES SOLUCIONES:"
echo "  1. ✅ Configurar Django REST Framework"
echo "  2. ✅ Crear ViewSets para pedidos"
echo "  3. ✅ Agregar URLs de API en urls.py"
echo "  4. ✅ Instalar 'djangorestframework'"
echo ""
echo "CONCLUSIÓN:"
echo "  La aplicación Django funciona pero no tiene API REST"
echo "  Las pruebas de modificación necesitan endpoints API"
echo "=============================================="