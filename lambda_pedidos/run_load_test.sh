#!/bin/bash

###############################################################################
# Script para ejecutar pruebas de carga con Locust
# Servicio de Pedidos - Lambda Function URL
###############################################################################

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║       🚀 PRUEBAS DE CARGA - SERVICIO DE PEDIDOS            ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que Locust esté instalado
if ! command -v locust &> /dev/null; then
    echo "❌ Locust no está instalado"
    echo ""
    echo "📦 Instala Locust con:"
    echo "   pip install locust"
    echo ""
    exit 1
fi

echo "✅ Locust encontrado: $(locust --version)"
echo ""

# Configuración
LAMBDA_URL="https://txsntfwdg3cmiliy7d2uo343by0gyzcp.lambda-url.us-east-1.on.aws"
LOCUST_FILE="locustfile.py"

# Menú de opciones
echo "Selecciona el tipo de prueba:"
echo ""
echo "1️⃣  Interfaz Web (recomendado) - Control manual de usuarios y duración"
echo "2️⃣  Prueba Rápida - 10 usuarios, 2 min"
echo "3️⃣  Prueba Media - 50 usuarios, 5 min"
echo "4️⃣  Prueba Intensiva - 100 usuarios, 10 min"
echo "5️⃣  Prueba Personalizada"
echo ""
read -p "Opción (1-5): " option

case $option in
    1)
        echo ""
        echo "🌐 Iniciando Locust con interfaz web..."
        echo "📍 Abre tu navegador en: http://localhost:8089"
        echo ""
        echo "💡 Configuración sugerida:"
        echo "   - Usuarios: 20-50 para pruebas moderadas"
        echo "   - Spawn rate: 5-10 usuarios/segundo"
        echo "   - Duration: 3-10 minutos"
        echo ""
        locust -f "$LOCUST_FILE" --host="$LAMBDA_URL"
        ;;
    2)
        echo ""
        echo "⚡ Ejecutando prueba rápida..."
        echo "👥 Usuarios: 10"
        echo "📈 Spawn rate: 2 usuarios/seg"
        echo "⏱️  Duración: 2 minutos"
        echo ""
        locust -f "$LOCUST_FILE" \
            --host="$LAMBDA_URL" \
            --users 10 \
            --spawn-rate 2 \
            --run-time 2m \
            --headless \
            --html report_rapido.html
        
        echo ""
        echo "✅ Prueba completada"
        echo "📊 Reporte: report_rapido.html"
        ;;
    3)
        echo ""
        echo "📊 Ejecutando prueba media..."
        echo "👥 Usuarios: 50"
        echo "📈 Spawn rate: 5 usuarios/seg"
        echo "⏱️  Duración: 5 minutos"
        echo ""
        locust -f "$LOCUST_FILE" \
            --host="$LAMBDA_URL" \
            --users 50 \
            --spawn-rate 5 \
            --run-time 5m \
            --headless \
            --html report_medio.html
        
        echo ""
        echo "✅ Prueba completada"
        echo "📊 Reporte: report_medio.html"
        ;;
    4)
        echo ""
        echo "🔥 Ejecutando prueba intensiva..."
        echo "👥 Usuarios: 100"
        echo "📈 Spawn rate: 10 usuarios/seg"
        echo "⏱️  Duración: 10 minutos"
        echo ""
        locust -f "$LOCUST_FILE" \
            --host="$LAMBDA_URL" \
            --users 100 \
            --spawn-rate 10 \
            --run-time 10m \
            --headless \
            --html report_intensivo.html
        
        echo ""
        echo "✅ Prueba completada"
        echo "📊 Reporte: report_intensivo.html"
        ;;
    5)
        echo ""
        read -p "👥 Número de usuarios: " users
        read -p "📈 Spawn rate (usuarios/seg): " spawn_rate
        read -p "⏱️  Duración (ej: 5m, 300s): " duration
        
        echo ""
        echo "🎯 Ejecutando prueba personalizada..."
        echo "👥 Usuarios: $users"
        echo "📈 Spawn rate: $spawn_rate usuarios/seg"
        echo "⏱️  Duración: $duration"
        echo ""
        
        locust -f "$LOCUST_FILE" \
            --host="$LAMBDA_URL" \
            --users "$users" \
            --spawn-rate "$spawn_rate" \
            --run-time "$duration" \
            --headless \
            --html report_personalizado.html
        
        echo ""
        echo "✅ Prueba completada"
        echo "📊 Reporte: report_personalizado.html"
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ PRUEBA FINALIZADA                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Si se generó un reporte HTML, intentar abrirlo
if [ -f "report_rapido.html" ] || [ -f "report_medio.html" ] || [ -f "report_intensivo.html" ] || [ -f "report_personalizado.html" ]; then
    echo "💡 Abre el archivo HTML en tu navegador para ver el reporte detallado"
    echo ""
fi
