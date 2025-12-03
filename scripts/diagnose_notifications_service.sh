#!/bin/bash
# Script de diagnóstico del servicio de notificaciones
# Ejecutar EN la instancia de notificaciones

echo "=========================================="
echo "  Estado del Servicio de Notificaciones"
echo "=========================================="

echo "1. Verificar si el servicio está corriendo:"
ps aux | grep "[u]vicorn" || echo "❌ No hay proceso uvicorn corriendo"

echo ""
echo "2. Verificar puerto 8001:"
netstat -tuln | grep 8001 || echo "❌ Puerto 8001 no está escuchando"

echo ""
echo "3. Verificar logs del servicio:"
if [ -f /home/ubuntu/notifications.log ]; then
    echo "Últimas 20 líneas de notifications.log:"
    tail -20 /home/ubuntu/notifications.log
else
    echo "❌ No existe /home/ubuntu/notifications.log"
fi

echo ""
echo "4. Verificar variables de entorno:"
grep "MONGO\|SECRET" /etc/environment

echo ""
echo "5. Probar el servicio localmente:"
curl -s http://localhost:8001/health && echo "" || echo "❌ No responde en localhost:8001"

echo ""
echo "6. Verificar conectividad a MongoDB:"
MONGO_HOST=$(grep MONGO_HOST /etc/environment | cut -d'=' -f2 | tr -d '"' | tr -d "'")
if [ -n "$MONGO_HOST" ]; then
    echo "MongoDB Host: $MONGO_HOST"
    nc -zv $MONGO_HOST 27017 2>&1
else
    echo "❌ MONGO_HOST no está configurado"
fi

echo ""
echo "=========================================="
echo "  Comandos para reiniciar el servicio:"
echo "=========================================="
echo "cd /home/ubuntu/Inventario/notifications"
echo "source /etc/environment"
echo "pkill -f uvicorn"
echo "nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /home/ubuntu/notifications.log 2>&1 &"
