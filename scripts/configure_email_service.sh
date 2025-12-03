#!/bin/bash
# Script para configurar el envío de correos en el servicio de notificaciones
# Ejecutar EN la instancia de notificaciones

echo "=========================================="
echo "  Configurar Envío de Correos"
echo "=========================================="

# Solicitar credenciales
read -p "Correo Gmail (para enviar): " GMAIL_USER
read -sp "App Password de Gmail: " GMAIL_PASSWORD
echo ""

# Configurar variables
export EMAIL_ENABLED="true"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="$GMAIL_USER"
export SMTP_PASSWORD="$GMAIL_PASSWORD"
export SENDER_EMAIL="$GMAIL_USER"
export DEFAULT_RECIPIENT="p.sanin@uniandes.edu.co"

# Guardar en /etc/environment
echo "Guardando configuración..."
sudo sed -i '/EMAIL_ENABLED/d' /etc/environment 2>/dev/null || true
sudo sed -i '/SMTP_/d' /etc/environment 2>/dev/null || true
sudo sed -i '/SENDER_EMAIL/d' /etc/environment 2>/dev/null || true
sudo sed -i '/DEFAULT_RECIPIENT/d' /etc/environment 2>/dev/null || true

echo "EMAIL_ENABLED=true" | sudo tee -a /etc/environment
echo "SMTP_HOST=smtp.gmail.com" | sudo tee -a /etc/environment
echo "SMTP_PORT=587" | sudo tee -a /etc/environment
echo "SMTP_USER=$GMAIL_USER" | sudo tee -a /etc/environment
echo "SMTP_PASSWORD=$GMAIL_PASSWORD" | sudo tee -a /etc/environment
echo "SENDER_EMAIL=$GMAIL_USER" | sudo tee -a /etc/environment
echo "DEFAULT_RECIPIENT=p.sanin@uniandes.edu.co" | sudo tee -a /etc/environment

echo "✅ Variables configuradas"

# Reiniciar servicio
echo ""
echo "Reiniciando servicio de notificaciones..."
cd /home/ubuntu/Inventario/notifications
source venv/bin/activate
source /etc/environment

pkill -f uvicorn || echo "No había proceso corriendo"
sleep 2

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /home/ubuntu/notifications.log 2>&1 &

sleep 3

echo ""
echo "=========================================="
echo "  ✅ Configuración Completada"
echo "=========================================="
echo ""
echo "El servicio ahora enviará correos a: p.sanin@uniandes.edu.co"
echo ""
echo "Verificar logs:"
echo "  tail -f /home/ubuntu/notifications.log"
