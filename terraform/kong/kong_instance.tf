# ==========================================
# KONG API GATEWAY - EC2 INSTANCE
# ==========================================

resource "aws_instance" "kong_gateway" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.kong_instance_type
  vpc_security_group_ids      = [aws_security_group.kong.id]
  associate_public_ip_address = true  # Para administración inicial
  
  user_data = <<-EOT
    #!/bin/bash
    exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
    echo "========================================"
    echo "CONFIGURANDO KONG API GATEWAY"
    echo "$(date): Iniciando configuración..."
    echo "========================================"
    
    # Actualizar sistema
    sudo apt-get update -y
    sudo apt-get upgrade -y
    
    # Instalar dependencias
    sudo apt-get install -y curl wget gnupg2 software-properties-common
    
    # Instalar Kong OSS 3.5
    echo "🦍 Descargando Kong Gateway..."
    wget -O kong.deb "https://download.konghq.com/gateway-3.x-ubuntu-noble/pool/all/k/kong/kong_${var.kong_version}_amd64.deb"
    sudo dpkg -i kong.deb || sudo apt-get install -f -y
    
    # Crear directorios y configuración
    sudo mkdir -p /etc/kong
    sudo mkdir -p /var/log/kong
    
    # Configurar variables de entorno Kong
    sudo tee /etc/kong/kong.conf > /dev/null <<'KONGCONF'
# Kong Configuration
database = off
declarative_config = /etc/kong/kong.yml
proxy_listen = 0.0.0.0:8000, 0.0.0.0:8443 ssl
admin_listen = 127.0.0.1:8001
log_level = ${var.kong_log_level}
error_log = /var/log/kong/error.log
access_log = /var/log/kong/access.log
KONGCONF
    
    # Configurar kong.yml temporal (se actualizará después)
    sudo tee /etc/kong/kong.yml > /dev/null <<'KONGYML'
_format_version: "3.0"
services:
  - name: kong-health
    url: http://localhost:8001
    routes:
      - name: health
        paths:
          - /status
KONGYML
    
    # Configurar permisos
    sudo chown -R kong:kong /etc/kong
    sudo chown -R kong:kong /var/log/kong
    
    # Crear servicio systemd para Kong
    sudo tee /etc/systemd/system/kong.service > /dev/null <<'KONGSERVICE'
[Unit]
Description=Kong API Gateway
After=network.target

[Service]
Type=forking
User=kong
Group=kong
Environment=KONG_CONF=/etc/kong/kong.conf
ExecStart=/usr/local/bin/kong start -c /etc/kong/kong.conf
ExecReload=/usr/local/bin/kong reload -c /etc/kong/kong.conf
ExecStop=/usr/local/bin/kong stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
KONGSERVICE
    
    # Habilitar e iniciar Kong
    sudo systemctl daemon-reload
    sudo systemctl enable kong
    sudo systemctl start kong
    
    # Esperar a que Kong inicie
    echo "⏳ Esperando a que Kong inicie..."
    for i in {1..30}; do
        if curl -f http://localhost:8001/status >/dev/null 2>&1; then
            echo "✅ Kong iniciado correctamente"
            break
        fi
        echo "Intento $i/30 - esperando Kong..."
        sleep 2
    done
    
    # Verificar health
    if curl -f http://localhost:8001/status >/dev/null 2>&1; then
        echo "🦍 Kong Gateway configurado exitosamente"
        echo "Admin API: http://localhost:8001"
        echo "Proxy: http://localhost:8000"
    else
        echo "❌ Error: Kong no pudo iniciar correctamente"
        sudo systemctl status kong
        sudo cat /var/log/kong/error.log
        exit 1
    fi
    
    echo "========================================"
    echo "KONG GATEWAY CONFIGURADO"
    echo "$(date): Configuración completada"
    echo "========================================"
  EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-gateway"
    Role = "api-gateway"
  })
}