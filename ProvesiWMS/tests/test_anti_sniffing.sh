#!/bin/bash

# Pruebas Automatizadas Anti-Sniffing para ProvesiWMS
# Este script verifica protecciones contra ataques de sniffing

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SERVER_URL="provesi-alb-2003818714.us-east-1.elb.amazonaws.com"
HTTP_URL="http://$SERVER_URL"
HTTPS_URL="https://$SERVER_URL"

echo -e "${BLUE}🛡️  INICIANDO PRUEBAS ANTI-SNIFFING${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Servidor: $SERVER_URL"
echo ""

# Función para verificar comando
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 no está instalado${NC}"
        return 1
    fi
    return 0
}

# Verificar dependencias
echo -e "${YELLOW}🔧 Verificando dependencias...${NC}"
check_command curl || exit 1
check_command openssl || exit 1
echo -e "${GREEN}✅ Dependencias verificadas${NC}"
echo ""

# Test 1: Verificar forzado de HTTPS
echo -e "${BLUE}🔐 Test 1: Verificando forzado de HTTPS${NC}"
echo "Intentando conexión HTTP..."
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -L "$HTTP_URL/inventario/" --max-time 10)

if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ]; then
    echo -e "${GREEN}✅ HTTP redirige a HTTPS (Código: $HTTP_RESPONSE)${NC}"
elif [ "$HTTP_RESPONSE" = "404" ] || [ "$HTTP_RESPONSE" = "403" ]; then
    echo -e "${GREEN}✅ HTTP rechazado correctamente (Código: $HTTP_RESPONSE)${NC}"
else
    echo -e "${RED}❌ HTTP no protegido adecuadamente (Código: $HTTP_RESPONSE)${NC}"
fi
echo ""

# Test 2: Verificar headers de seguridad HTTPS
echo -e "${BLUE}🛡️  Test 2: Verificando headers de seguridad${NC}"
echo "Obteniendo headers HTTPS..."

HEADERS=$(curl -s -I "$HTTPS_URL/inventario/" --max-time 10 -k)

# Verificar HSTS
if echo "$HEADERS" | grep -i "strict-transport-security" > /dev/null; then
    HSTS=$(echo "$HEADERS" | grep -i "strict-transport-security" | head -1)
    echo -e "${GREEN}✅ HSTS configurado: ${HSTS#*: }${NC}"
else
    echo -e "${RED}❌ HSTS no configurado${NC}"
fi

# Verificar X-Content-Type-Options
if echo "$HEADERS" | grep -i "x-content-type-options.*nosniff" > /dev/null; then
    echo -e "${GREEN}✅ X-Content-Type-Options: nosniff${NC}"
else
    echo -e "${YELLOW}⚠️  X-Content-Type-Options no configurado${NC}"
fi

# Verificar X-Frame-Options
if echo "$HEADERS" | grep -i "x-frame-options" > /dev/null; then
    XFRAME=$(echo "$HEADERS" | grep -i "x-frame-options" | head -1)
    echo -e "${GREEN}✅ X-Frame-Options configurado: ${XFRAME#*: }${NC}"
else
    echo -e "${YELLOW}⚠️  X-Frame-Options no configurado${NC}"
fi

# Verificar Server header (debe estar oculto o genérico)
if echo "$HEADERS" | grep -i "server:" > /dev/null; then
    SERVER_HEADER=$(echo "$HEADERS" | grep -i "server:" | head -1)
    if echo "$SERVER_HEADER" | grep -E "(apache/[0-9]|nginx/[0-9]|django|python)" > /dev/null; then
        echo -e "${RED}❌ Server header revela información: ${SERVER_HEADER#*: }${NC}"
    else
        echo -e "${GREEN}✅ Server header genérico: ${SERVER_HEADER#*: }${NC}"
    fi
else
    echo -e "${GREEN}✅ Server header oculto${NC}"
fi
echo ""

# Test 3: Verificar configuración SSL/TLS
echo -e "${BLUE}🔒 Test 3: Verificando configuración SSL/TLS${NC}"
echo "Analizando certificado SSL..."

SSL_INFO=$(echo | openssl s_client -connect "$SERVER_URL:443" -servername "$SERVER_URL" 2>/dev/null)

if echo "$SSL_INFO" | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✅ Certificado SSL válido${NC}"
else
    echo -e "${RED}❌ Problemas con certificado SSL${NC}"
fi

# Verificar versión TLS
TLS_VERSION=$(echo "$SSL_INFO" | grep "Protocol" | head -1 | awk '{print $3}')
if [ -n "$TLS_VERSION" ]; then
    if [[ "$TLS_VERSION" == "TLSv1.2" ]] || [[ "$TLS_VERSION" == "TLSv1.3" ]]; then
        echo -e "${GREEN}✅ TLS versión segura: $TLS_VERSION${NC}"
    else
        echo -e "${RED}❌ TLS versión insegura: $TLS_VERSION${NC}"
    fi
fi

# Verificar cipher suite
CIPHER=$(echo "$SSL_INFO" | grep "Cipher" | head -1 | awk '{print $3}')
if [ -n "$CIPHER" ]; then
    echo -e "${GREEN}✅ Cipher suite: $CIPHER${NC}"
fi
echo ""

# Test 4: Probar login con credenciales falsas
echo -e "${BLUE}🕵️  Test 4: Verificando manejo de errores${NC}"
echo "Probando login con credenciales falsas..."

ERROR_RESPONSE=$(curl -s -X POST "$HTTPS_URL/inventario/auth/token/" \
    -H "Content-Type: application/json" \
    -d '{"username":"usuario_falso","password":"password_falso"}' \
    --max-time 10 -k)

# Verificar que no revela información sensible
if echo "$ERROR_RESPONSE" | grep -i -E "(traceback|django|python|exception|stack|database|sql)" > /dev/null; then
    echo -e "${RED}❌ Error revela información sensible${NC}"
    echo "Información expuesta: $(echo "$ERROR_RESPONSE" | grep -i -o -E "(traceback|django|python|exception|stack|database|sql)" | head -3)"
else
    echo -e "${GREEN}✅ Errores no revelan información sensible${NC}"
fi
echo ""

# Test 5: Probar endpoint no existente
echo -e "${BLUE}🔍 Test 5: Verificando páginas 404${NC}"
echo "Probando endpoint inexistente..."

NOT_FOUND_RESPONSE=$(curl -s "$HTTPS_URL/inventario/endpoint-que-no-existe/" --max-time 10 -k)

if echo "$NOT_FOUND_RESPONSE" | grep -i -E "(urls\.py|views\.py|models\.py|/home/|/var/www/|django\.contrib)" > /dev/null; then
    echo -e "${RED}❌ Página 404 revela estructura interna${NC}"
else
    echo -e "${GREEN}✅ Página 404 no revela información interna${NC}"
fi
echo ""

# Test 6: Verificar login válido HTTPS
echo -e "${BLUE}🔐 Test 6: Verificando login válido via HTTPS${NC}"
echo "Probando login con credenciales válidas..."

LOGIN_RESPONSE=$(curl -s -X POST "$HTTPS_URL/inventario/auth/token/" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"ProvesiAdmin2024!"}' \
    --max-time 10 -k)

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    echo -e "${GREEN}✅ Login exitoso via HTTPS${NC}"
    
    # Verificar que el token es un JWT válido
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$ACCESS_TOKEN" ]; then
        JWT_PARTS=$(echo "$ACCESS_TOKEN" | tr '.' '\n' | wc -l)
        if [ "$JWT_PARTS" -eq 3 ]; then
            echo -e "${GREEN}✅ Token JWT válido retornado${NC}"
        else
            echo -e "${RED}❌ Token JWT malformado${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Login falló - verificar credenciales${NC}"
fi
echo ""

# Resumen final
echo -e "${BLUE}📊 RESUMEN DE PROTECCIONES ANTI-SNIFFING${NC}"
echo -e "${BLUE}=========================================${NC}"

SECURITY_SCORE=0
TOTAL_TESTS=6

# Verificar cada protección y calcular score
if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ] || [ "$HTTP_RESPONSE" = "404" ] || [ "$HTTP_RESPONSE" = "403" ]; then
    echo -e "${GREEN}✅ HTTPS forzado${NC}"
    ((SECURITY_SCORE++))
else
    echo -e "${RED}❌ HTTPS no forzado${NC}"
fi

if echo "$HEADERS" | grep -i "strict-transport-security" > /dev/null; then
    echo -e "${GREEN}✅ HSTS configurado${NC}"
    ((SECURITY_SCORE++))
else
    echo -e "${RED}❌ HSTS no configurado${NC}"
fi

if echo "$SSL_INFO" | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✅ Certificado SSL válido${NC}"
    ((SECURITY_SCORE++))
else
    echo -e "${RED}❌ Certificado SSL inválido${NC}"
fi

if ! echo "$ERROR_RESPONSE" | grep -i -E "(traceback|django|python|exception|stack)" > /dev/null; then
    echo -e "${GREEN}✅ Errores seguros${NC}"
    ((SECURITY_SCORE++))
else
    echo -e "${RED}❌ Errores revelan información${NC}"
fi

if ! echo "$NOT_FOUND_RESPONSE" | grep -i -E "(urls\.py|views\.py|models\.py)" > /dev/null; then
    echo -e "${GREEN}✅ Páginas 404 seguras${NC}"
    ((SECURITY_SCORE++))
else
    echo -e "${RED}❌ Páginas 404 revelan estructura${NC}"
fi

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    echo -e "${GREEN}✅ Login HTTPS funcional${NC}"
    ((SECURITY_SCORE++))
else
    echo -e "${YELLOW}⚠️  Login necesita verificación${NC}"
fi

echo ""
echo -e "${BLUE}🎯 PUNTUACIÓN DE SEGURIDAD: $SECURITY_SCORE/$TOTAL_TESTS${NC}"

if [ "$SECURITY_SCORE" -eq "$TOTAL_TESTS" ]; then
    echo -e "${GREEN}🏆 EXCELENTE: Sistema completamente protegido contra sniffing${NC}"
elif [ "$SECURITY_SCORE" -ge $((TOTAL_TESTS * 3 / 4)) ]; then
    echo -e "${YELLOW}🥈 BUENO: Sistema mayormente protegido, algunas mejoras recomendadas${NC}"
else
    echo -e "${RED}🚨 CRÍTICO: Sistema vulnerable a ataques de sniffing${NC}"
fi

echo ""
echo -e "${BLUE}📋 RECOMENDACIONES:${NC}"
echo -e "🔒 Asegurar que todo el tráfico sea HTTPS"
echo -e "🛡️  Configurar todos los headers de seguridad"
echo -e "🔐 Usar certificados SSL válidos"
echo -e "🕵️ Ocultar información sensible en errores"
echo -e "🚫 No revelar estructura interna de la aplicación"

exit 0