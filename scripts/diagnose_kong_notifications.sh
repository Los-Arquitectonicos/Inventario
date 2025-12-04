#!/bin/bash
# Script de diagnóstico rápido del servicio de notificaciones
# Ejecutar EN la instancia de Kong

echo "=========================================="
echo "  Diagnóstico Servicio Notificaciones"
echo "=========================================="

# Verificar kong.yaml
echo "1. Configuración en kong.yaml:"
grep -A 5 "notifications-service" /home/ubuntu/kong.yaml

echo ""
echo "2. Verificar conectividad desde Kong al servicio:"

# Obtener IP del servicio de notificaciones
NOTIF_IP=$(grep "notifications-service" /home/ubuntu/kong.yaml -A 1 | grep "url:" | sed 's/.*http:\/\/\([^:]*\).*/\1/')

if [ -z "$NOTIF_IP" ]; then
    echo "❌ No se pudo encontrar IP de notificaciones en kong.yaml"
else
    echo "IP de notificaciones: $NOTIF_IP"
    echo ""
    echo "Probando conectividad al puerto 8001..."
    nc -zv $NOTIF_IP 8001 2>&1 || echo "❌ No se puede conectar al puerto 8001"
    
    echo ""
    echo "Probando endpoint /health directamente:"
    curl -s http://$NOTIF_IP:8001/health || echo "❌ No responde"
fi

echo ""
echo "3. Estado del contenedor Kong:"
sudo docker ps --filter "name=kong" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "4. Logs recientes de Kong:"
sudo docker logs --tail 20 $(sudo docker ps -q --filter "name=kong")

echo ""
echo "=========================================="
echo "  Comandos útiles:"
echo "=========================================="
echo "Reiniciar Kong:"
echo "  sudo docker restart \$(sudo docker ps -q --filter \"name=kong\")"
echo ""
echo "Ver logs en tiempo real:"
echo "  sudo docker logs -f \$(sudo docker ps -q --filter \"name=kong\")"
