# ==========================================
# KONG API GATEWAY - EC2 INSTANCE
# ==========================================
# ProvesiWMS Service Discovery
# ==========================================

# Instancia EC2 para Kong Gateway
resource "aws_instance" "kong_gateway" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.kong_instance_type
  vpc_security_group_ids      = [aws_security_group.kong.id]
  associate_public_ip_address = true # Para SSH de administración
  key_name                    = var.key_pair_name != "" ? var.key_pair_name : null

  user_data = <<-EOT
              #!/bin/bash
              set -e
              
              # ==========================================
              # KONG GATEWAY INSTALLATION SCRIPT
              # ==========================================
              
              # Log de instalación
              exec > >(tee /var/log/kong-install.log|logger -t kong-install -s 2>/dev/console) 2>&1
              echo "=========================================="
              echo "INSTALANDO KONG API GATEWAY"
              echo "$(date): Iniciando instalación..."
              echo "=========================================="
              
              # Variables de configuración
              KONG_VERSION="${var.kong_version}"
              DJANGO_SERVER_1="${aws_instance.app_server[0].private_ip}"
              DJANGO_SERVER_2="${length(aws_instance.app_server) > 1 ? aws_instance.app_server[1].private_ip : aws_instance.app_server[0].private_ip}"
              
              # Actualizar sistema
              echo "$(date): Actualizando sistema..."
              sudo apt-get update -y
              sudo apt-get upgrade -y
              
              # Instalar dependencias
              sudo apt-get install -y curl wget gnupg lsb-release jq
              
              # Crear directorios para logs
              sudo mkdir -p /var/log/kong
              sudo chown -R ubuntu:ubuntu /var/log/kong
              
              # ==========================================
              # INSTALAR KONG OSS
              # ==========================================
              echo "$(date): Instalando Kong Gateway OSS $${KONG_VERSION}..."
              
              # Agregar repositorio de Kong
              curl -1sLf "https://packages.konghq.com/public/gateway-35/gpg.59266503870919B5.key" | \
                sudo gpg --dearmor -o /usr/share/keyrings/kong-gateway-35-archive-keyring.gpg
              
              echo "deb [signed-by=/usr/share/keyrings/kong-gateway-35-archive-keyring.gpg] https://packages.konghq.com/public/gateway-35/deb/ubuntu $(lsb_release -cs) main" | \
                sudo tee /etc/apt/sources.list.d/kong-gateway-35.list > /dev/null
              
              sudo apt-get update -y
              sudo apt-get install -y kong-enterprise-edition || sudo apt-get install -y kong
              
              # ==========================================
              # CONFIGURAR KONG
              # ==========================================
              echo "$(date): Configurando Kong..."
              
              # Crear directorio de configuración
              sudo mkdir -p /etc/kong
              
              # Crear archivo de configuración principal
              sudo tee /etc/kong/kong.conf > /dev/null <<'KONGCONF'
# Kong Configuration - ProvesiWMS
database = off
declarative_config = /etc/kong/kong.yml

proxy_listen = 0.0.0.0:8000
admin_listen = 127.0.0.1:8001
status_listen = 0.0.0.0:8100

log_level = ${var.kong_log_level}
proxy_access_log = /var/log/kong/access.log
proxy_error_log = /var/log/kong/error.log
admin_access_log = /var/log/kong/admin_access.log
admin_error_log = /var/log/kong/admin_error.log

nginx_worker_processes = auto
upstream_keepalive_pool_size = 60
upstream_keepalive_max_requests = 100
upstream_keepalive_idle_timeout = 60

headers = off
trusted_ips = 0.0.0.0/0,::/0
real_ip_header = X-Forwarded-For
real_ip_recursive = on

plugins = bundled
KONGCONF

              # Crear configuración declarativa con IPs reales de Django
              sudo tee /etc/kong/kong.yml > /dev/null <<KONGYML
_format_version: "3.0"
_transform: true

# ==========================================
# SERVICES & ROUTES
# ==========================================

services:
  # Django Backend API
  - name: django-api
    host: django-upstream
    port: 8000
    protocol: http
    retries: 3
    connect_timeout: 5000
    write_timeout: 60000
    read_timeout: 60000
    
    routes:
      - name: django-api-route
        paths:
          - /api
          - /inventario
          - /admin
        strip_path: false
        preserve_host: true
        methods:
          - GET
          - POST
          - PUT
          - PATCH
          - DELETE
          - OPTIONS
        
    plugins:
      - name: rate-limiting
        config:
          minute: 200
          policy: local
          fault_tolerant: true
          
      - name: cors
        config:
          origins:
            - "*"
          methods:
            - GET
            - POST
            - PUT
            - PATCH
            - DELETE
            - OPTIONS
          headers:
            - Accept
            - Authorization
            - Content-Type
            - X-Requested-With
            - X-Kong-Request-ID
          exposed_headers:
            - X-Kong-Request-ID
          credentials: true
          max_age: 3600

# ==========================================
# UPSTREAMS
# ==========================================

upstreams:
  - name: django-upstream
    algorithm: round-robin
    healthchecks:
      active:
        healthy:
          interval: 10
          successes: 2
        unhealthy:
          interval: 5
          http_failures: 3
        http_path: /inventario/
        timeout: 5
        type: http
      passive:
        healthy:
          successes: 2
        unhealthy:
          http_failures: 3
    
    targets:
      - target: $${DJANGO_SERVER_1}:8000
        weight: 100
      - target: $${DJANGO_SERVER_2}:8000
        weight: 100

# ==========================================
# GLOBAL PLUGINS
# ==========================================

plugins:
  - name: correlation-id
    config:
      header_name: X-Kong-Request-ID
      generator: uuid
      echo_downstream: true
  
  - name: file-log
    config:
      path: /var/log/kong/access.log
      reopen: true
KONGYML

              # ==========================================
              # CREAR SERVICIO SYSTEMD
              # ==========================================
              echo "$(date): Configurando servicio systemd..."
              
              sudo tee /etc/systemd/system/kong.service > /dev/null <<'SYSTEMD'
[Unit]
Description=Kong API Gateway
After=network.target

[Service]
Type=forking
User=root
ExecStartPre=/usr/local/bin/kong check /etc/kong/kong.conf
ExecStart=/usr/local/bin/kong start -c /etc/kong/kong.conf
ExecReload=/usr/local/bin/kong reload -c /etc/kong/kong.conf
ExecStop=/usr/local/bin/kong stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SYSTEMD

              # Recargar systemd
              sudo systemctl daemon-reload
              
              # ==========================================
              # INICIAR KONG
              # ==========================================
              echo "$(date): Iniciando Kong..."
              
              # Esperar a que los servidores Django estén listos
              echo "$(date): Esperando a servidores Django..."
              for i in {1..30}; do
                if curl -sf "http://$${DJANGO_SERVER_1}:8000/inventario/" > /dev/null 2>&1; then
                  echo "$(date): Django server 1 está listo"
                  break
                fi
                echo "$(date): Esperando Django... intento $i/30"
                sleep 10
              done
              
              # Iniciar Kong
              sudo kong start -c /etc/kong/kong.conf || {
                echo "$(date): Error iniciando Kong, verificando configuración..."
                sudo kong check /etc/kong/kong.conf
                exit 1
              }
              
              # Habilitar inicio automático
              sudo systemctl enable kong
              
              # ==========================================
              # VERIFICACIÓN
              # ==========================================
              echo "$(date): Verificando instalación..."
              
              # Esperar a que Kong esté listo
              sleep 5
              
              # Health check
              if curl -sf http://localhost:8100/status > /dev/null; then
                echo "$(date): ✅ Kong está funcionando correctamente"
              else
                echo "$(date): ⚠️ Kong puede no estar completamente listo"
              fi
              
              # Mostrar información
              echo ""
              echo "=========================================="
              echo "$(date): ✅ INSTALACIÓN COMPLETADA"
              echo "=========================================="
              echo "Kong Version: $(kong version)"
              echo "Proxy Port: 8000"
              echo "Admin API: localhost:8001"
              echo "Status Port: 8100"
              echo ""
              echo "Servidores Django configurados:"
              echo "  - $${DJANGO_SERVER_1}:8000"
              echo "  - $${DJANGO_SERVER_2}:8000"
              echo ""
              echo "Comandos útiles:"
              echo "  - Ver estado: sudo kong health"
              echo "  - Ver logs: sudo tail -f /var/log/kong/access.log"
              echo "  - Recargar: sudo kong reload"
              echo "=========================================="
              
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-gateway"
    Role = "api-gateway"
  })

  depends_on = [aws_instance.app_server]
}
