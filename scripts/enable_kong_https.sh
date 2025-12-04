#!/bin/bash
# Script para habilitar HTTPS en Kong (instancia existente)
# Ejecutar directamente en la instancia Kong vía EC2 Instance Connect

set -e

echo "=== Habilitando HTTPS en Kong ==="

# 1. Crear directorio para certificados
echo "1. Creando directorio para certificados..."
sudo mkdir -p /opt/kong/certs
cd /opt/kong/certs

# 2. Generar certificado SSL self-signed
echo "2. Generando certificado SSL..."
sudo openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout kong-key.pem \
  -out kong-cert.pem \
  -days 365 \
  -subj "/CN=kong-gateway/O=Provesi WMS"

# Cambiar permisos para que Kong pueda leer los certificados
sudo chmod 644 kong-cert.pem
sudo chmod 644 kong-key.pem

echo "✅ Certificado generado"
ls -lh /opt/kong/certs/

# 3. Detener y eliminar el contenedor Kong actual
echo "3. Deteniendo Kong actual..."
sudo docker stop kong || true
sudo docker rm kong || true

# 4. Recrear Kong con HTTPS habilitado
echo "4. Iniciando Kong con HTTPS..."
sudo docker run -d --name kong --network=kong-net --restart=always \
  --user root \
  -v "/opt/kong/Inventario:/kong/declarative/" \
  -v "/opt/kong/certs:/kong/certs/" \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yaml" \
  -e "KONG_SSL_CERT=/kong/certs/kong-cert.pem" \
  -e "KONG_SSL_CERT_KEY=/kong/certs/kong-key.pem" \
  -e "KONG_PROXY_LISTEN=0.0.0.0:8000, 0.0.0.0:8443 ssl" \
  -p 8000:8000 \
  -p 8443:8443 \
  kong/kong-gateway

# 5. Esperar y verificar logs
echo "5. Esperando inicio de Kong..."
sleep 5

echo ""
echo "=== Logs de Kong ==="
sudo docker logs kong --tail 30

echo ""
echo "=== Configuración completada ==="
echo "Kong ahora escucha en:"
echo "  - HTTP:  http://<KONG_IP>:8000"
echo "  - HTTPS: https://<KONG_IP>:8443"
echo ""
echo "Verifica con:"
echo "  curl -k https://<KONG_IP>:8443/inventario/"
echo ""
echo "⚠️  Nota: El certificado es self-signed, usa -k con curl"
