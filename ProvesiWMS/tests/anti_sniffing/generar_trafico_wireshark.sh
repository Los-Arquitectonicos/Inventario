#!/bin/bash

# Script para generar tráfico mientras Wireshark captura
# Úsalo mientras tienes Wireshark ejecutándose

echo "Generando tráfico para análisis con Wireshark..."
echo "IMPORTANTE: Asegúrate de que Wireshark esté capturando primero!"
echo ""

BASE_URL="https://provesi-alb-696561682.us-east-1.elb.amazonaws.com"
HTTP_URL="http://provesi-alb-696561682.us-east-1.elb.amazonaws.com"

echo "Generando diferentes tipos de tráfico..."

# 1. Tráfico HTTP (debe redirigir a HTTPS)
echo "1. Probando HTTP (debe redirigir)..."
curl -v "$HTTP_URL/inventario/" 2>&1

sleep 2

# 2. Tráfico HTTPS normal
echo "2. Acceso HTTPS normal..."
curl -k -v "$BASE_URL/inventario/" 2>&1

sleep 2

# 3. Intento de login (datos sensibles)
echo "3. Intento de autenticación..."
curl -k -X POST "$BASE_URL/inventario/auth/token/" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}' \
     -v 2>&1

sleep 2

# 4. Acceso a datos de pedidos
echo "4. Acceso a pedidos..."
curl -k "$BASE_URL/inventario/pedidos/" -v 2>&1

sleep 2

# 5. Múltiples requests (simular sesión)
echo "5. Simulando sesión de usuario..."
for i in {1..5}; do
    curl -k -s "$BASE_URL/inventario/" > /dev/null
    sleep 1
done

echo ""
echo "Tráfico generado. Ahora detén la captura en Wireshark y analiza."