#!/bin/bash
# Script para reiniciar el servicio de notificaciones
# Ejecutar EN la instancia de notificaciones

set -e

echo "=========================================="
echo "  Reiniciar Servicio de Notificaciones"
echo "=========================================="

# 1. Detener proceso actual
echo "1. Deteniendo procesos uvicorn existentes..."
pkill -f "uvicorn.*main:app" || echo "   No hay procesos corriendo"

sleep 2

# 2. Verificar que se detuvo
if ps aux | grep -v grep | grep "uvicorn.*main:app" > /dev/null; then
    echo "   ⚠️  Proceso aún corriendo, forzando detención..."
    pkill -9 -f "uvicorn.*main:app"
    sleep 2
fi

# 3. Cargar variables de entorno
echo "2. Cargando variables de entorno..."
source /etc/environment

# Verificar variables críticas
if [ -z "$MONGO_HOST" ]; then
    echo "   ❌ MONGO_HOST no está definido"
    exit 1
fi

echo "   ✅ MONGO_HOST: $MONGO_HOST"

# 4. Ir al directorio del servicio
cd /home/ubuntu/Inventario/notifications

# 5. Iniciar el servicio
echo "3. Iniciando servicio de notificaciones en puerto 8001..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /home/ubuntu/notifications.log 2>&1 &

UVICORN_PID=$!
echo "   ✅ Proceso iniciado con PID: $UVICORN_PID"

# 6. Esperar a que inicie
echo "4. Esperando 5 segundos para que el servicio inicie..."
sleep 5

# 7. Verificar que está corriendo
echo "5. Verificando estado del servicio..."

if ps -p $UVICORN_PID > /dev/null; then
    echo "   ✅ Proceso corriendo (PID: $UVICORN_PID)"
else
    echo "   ❌ El proceso no está corriendo"
    echo "   Últimas líneas del log:"
    tail -20 /home/ubuntu/notifications.log
    exit 1
fi

# 8. Probar endpoint
echo "6. Probando endpoint /health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "   ✅ Servicio respondiendo correctamente"
    echo "   Respuesta: $HEALTH_RESPONSE"
else
    echo "   ❌ Servicio no responde correctamente"
    echo "   Respuesta: $HEALTH_RESPONSE"
    echo ""
    echo "   Últimas líneas del log:"
    tail -20 /home/ubuntu/notifications.log
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ Servicio Reiniciado Exitosamente"
echo "=========================================="
echo ""
echo "Información:"
echo "  PID: $UVICORN_PID"
echo "  Puerto: 8001"
echo "  Log: /home/ubuntu/notifications.log"
echo ""
echo "Ver logs en tiempo real:"
echo "  tail -f /home/ubuntu/notifications.log"
echo ""
echo "Verificar desde Kong:"
echo "  curl http://$(hostname -I | awk '{print $1}'):8001/health"
