#!/bin/bash

# Script de ejecución rápida para el test de pedidos GET
# Autor: Sistema de Inventario
# Uso: ./run_pedidos_test.sh

echo "🚀 EJECUTANDO TEST JMETER - SISTEMA DE PEDIDOS GET"
echo "================================================="

# Variables de configuración
HOST=${1:-127.0.0.1}
PORT=${2:-8001}
THREADS=${3:-15}
RAMP_TIME=${4:-20}
LOOPS=${5:-3}

echo "📋 Configuración del Test:"
echo "   🌐 Host: $HOST"
echo "   🔌 Puerto: $PORT"
echo "   👥 Usuarios concurrentes: $THREADS"
echo "   ⏱️  Tiempo de rampa: ${RAMP_TIME}s"
echo "   🔄 Iteraciones: $LOOPS"
echo ""

# Verificar si JMeter está instalado
if ! command -v jmeter &> /dev/null; then
    echo "❌ JMeter no está instalado o no está en el PATH"
    echo "💡 Instala JMeter desde: https://jmeter.apache.org/"
    exit 1
fi

# Verificar si el servidor Django está corriendo
echo "🔍 Verificando servidor Django..."
if curl -s "http://$HOST:$PORT/pedidos/" > /dev/null; then
    echo "✅ Servidor Django respondiendo en http://$HOST:$PORT"
else
    echo "❌ No se puede conectar al servidor Django"
    echo "💡 Asegúrate de que Django esté ejecutándose:"
    echo "   python manage.py runserver $PORT"
    exit 1
fi

# Verificar si existen datos de prueba
echo "🔍 Verificando datos de pedidos..."
RESPONSE=$(curl -s "http://$HOST:$PORT/pedidos/")
if echo "$RESPONSE" | grep -q '"pedidos"'; then
    PEDIDOS_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['pedidos']))" 2>/dev/null || echo "0")
    if [ "$PEDIDOS_COUNT" -gt 0 ]; then
        echo "✅ Encontrados $PEDIDOS_COUNT pedidos en el sistema"
    else
        echo "⚠️  No hay pedidos en el sistema"
        echo "💡 Ejecuta el script de datos de prueba:"
        echo "   python tests/create_orders_test_data.py"
        echo ""
        echo "🤔 ¿Continuar de todos modos? (s/n)"
        read -n 1 CONTINUE
        echo ""
        if [[ ! $CONTINUE =~ ^[Ss]$ ]]; then
            echo "❌ Test cancelado"
            exit 1
        fi
    fi
else
    echo "⚠️  No se puede verificar el endpoint de pedidos"
    echo "💡 Verifica que el servidor esté configurado correctamente"
fi

# Crear directorio de resultados
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="pedidos_test_results_$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

echo ""
echo "🎯 INICIANDO TEST DE PEDIDOS GET..."
echo "=================================="

# Ejecutar JMeter
jmeter -n \
    -t "tests/pedidos_get_test.jmx" \
    -Jserver.host="$HOST" \
    -Jserver.port="$PORT" \
    -Jthreads="$THREADS" \
    -Jramp.time="$RAMP_TIME" \
    -Jloops="$LOOPS" \
    -l "$RESULTS_DIR/results.jtl" \
    -e -o "$RESULTS_DIR/report/"

# Verificar si el test se ejecutó correctamente
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ TEST COMPLETADO EXITOSAMENTE"
    echo "==============================="
    echo "📊 Resultados guardados en: $RESULTS_DIR/"
    echo "🌐 Reporte HTML: $RESULTS_DIR/report/index.html"
    echo ""
    echo "📋 Endpoints Probados:"
    echo "   • GET /pedidos/ - Lista de pedidos"
    echo "   • GET /pedidos/{id}/ - Pedido específico"
    echo "   • GET /pedidos/{id}/detalles/ - Detalles del pedido"
    echo "   • GET /pedidos/{id}/ubicaciones/ - 🎯 FUNCIÓN PRINCIPAL"
    echo ""
    echo "🔍 Para ver el reporte:"
    echo "   open $RESULTS_DIR/report/index.html"
    echo ""
    
    # Mostrar resumen rápido si existe el archivo de resultados
    if [ -f "$RESULTS_DIR/results.jtl" ]; then
        echo "📊 RESUMEN RÁPIDO:"
        echo "=================="
        
        # Contar líneas (requests totales)
        TOTAL_REQUESTS=$(tail -n +2 "$RESULTS_DIR/results.jtl" | wc -l | tr -d ' ')
        echo "📈 Total de requests: $TOTAL_REQUESTS"
        
        # Contar errores (columna 8 = success, false = error)
        ERRORS=$(tail -n +2 "$RESULTS_DIR/results.jtl" | awk -F',' '$8=="false"' | wc -l | tr -d ' ')
        echo "❌ Errores: $ERRORS"
        
        # Calcular porcentaje de éxito
        if [ "$TOTAL_REQUESTS" -gt 0 ]; then
            SUCCESS_RATE=$(echo "scale=2; (($TOTAL_REQUESTS - $ERRORS) * 100) / $TOTAL_REQUESTS" | bc)
            echo "✅ Tasa de éxito: ${SUCCESS_RATE}%"
        fi
        
        echo ""
        echo "💡 Para análisis detallado, abre el reporte HTML"
    fi
    
else
    echo ""
    echo "❌ ERROR EN LA EJECUCIÓN DEL TEST"
    echo "================================="
    echo "🔍 Verifica:"
    echo "   • Que Django esté ejecutándose"
    echo "   • Que los endpoints estén disponibles"
    echo "   • Los logs de JMeter para detalles"
    exit 1
fi