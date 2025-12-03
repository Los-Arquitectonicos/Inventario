P# ==========================================
# KONG API GATEWAY - ÚNICO PUNTO DE ENTRADA
# ==========================================
# Arquitectura:
#   Internet → Kong (público) → ALB (interno) → Django Servers
#
# Kong es el ÚNICO punto de entrada público a todas las APIs.
# El ALB actúa como balanceador interno entre Kong y Django.
# ==========================================

# ==========================================
# SECURITY GROUP
# ==========================================

# Security Group para Kong Gateway (ÚNICO punto de entrada público)
resource "aws_security_group" "kong" {
  name        = "${var.project_prefix}-kong-sg"
  description = "Security group for Kong API Gateway - Public entry point"
  vpc_id      = data.aws_vpc.default.id

  # HTTPS público (puerto principal de entrada)
  ingress {
    description = "HTTPS public access"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP público (para pruebas o redirección)
  ingress {
    description = "HTTP public access"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Status/Health check público
  ingress {
    description = "Kong status public access"
    from_port   = 8100
    to_port     = 8100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH para administración
  ingress {
    description = "SSH for management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Permitir todo el tráfico saliente (Kong → ALB)
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-sg"
  })
}

# Regla: Permitir que Kong acceda al ALB (interno)
resource "aws_security_group_rule" "alb_from_kong" {
  security_group_id        = aws_security_group.alb.id
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access ALB"
}

# ==========================================
# EC2 INSTANCE - KONG GATEWAY
# ==========================================

resource "aws_instance" "kong_gateway" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.kong_instance_type
  vpc_security_group_ids      = [aws_security_group.kong.id]
  associate_public_ip_address = true
  key_name                    = var.key_pair_name != "" ? var.key_pair_name : null

  user_data = <<-EOT
              #!/bin/bash
              set -e
              
              # ==========================================
              # KONG GATEWAY - INSTALACIÓN AUTOMÁTICA
              # ==========================================
              
              exec > >(tee /var/log/kong-install.log|logger -t kong-install -s 2>/dev/console) 2>&1
              echo "=========================================="
              echo "INSTALANDO KONG API GATEWAY"
              echo "$$(date): Iniciando instalación..."
              echo "==========================================" 
              
              # Variable del ALB (backend interno)
              ALB_DNS="${aws_lb.main.dns_name}"
              
              # ==========================================
              # ACTUALIZAR SISTEMA
              # ==========================================
              echo "$$(date): Actualizando sistema..."
              sudo apt-get update -y
              sudo apt-get upgrade -y
              sudo apt-get install -y curl wget gnupg lsb-release jq openssl
              
              # Crear directorios
              sudo mkdir -p /var/log/kong
              sudo mkdir -p /etc/kong/ssl
              sudo chown -R ubuntu:ubuntu /var/log/kong
              
              # ==========================================
              # INSTALAR KONG
              # ==========================================
              echo "$$(date): Instalando Kong Gateway..."
              
              curl -1sLf "https://packages.konghq.com/public/gateway-35/gpg.59266503870919B5.key" | \
                sudo gpg --dearmor -o /usr/share/keyrings/kong-gateway-35-archive-keyring.gpg
              
              echo "deb [signed-by=/usr/share/keyrings/kong-gateway-35-archive-keyring.gpg] https://packages.konghq.com/public/gateway-35/deb/ubuntu $$(lsb_release -cs) main" | \
                sudo tee /etc/apt/sources.list.d/kong-gateway-35.list > /dev/null
              
              sudo apt-get update -y
              sudo apt-get install -y kong-enterprise-edition || sudo apt-get install -y kong
              
              # ==========================================
              # GENERAR CERTIFICADO SSL
              # ==========================================
              echo "$$(date): Generando certificado SSL..."
              sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout /etc/kong/ssl/kong.key \
                -out /etc/kong/ssl/kong.crt \
                -subj "/C=US/ST=State/L=City/O=ProvesiWMS/CN=kong.provesi.local"
              sudo chmod 600 /etc/kong/ssl/kong.key
              
              # ==========================================
              # CONFIGURACIÓN DE KONG
              # ==========================================
              echo "$$(date): Configurando Kong..."
              
              # kong.conf - Configuración del servidor
              sudo tee /etc/kong/kong.conf > /dev/null <<'KONGCONF'
# Kong API Gateway Configuration
database = off
declarative_config = /etc/kong/kong.yml

# Listeners
proxy_listen = 0.0.0.0:8000, 0.0.0.0:443 ssl
admin_listen = 127.0.0.1:8001
status_listen = 0.0.0.0:8100

# SSL
ssl_cert = /etc/kong/ssl/kong.crt
ssl_cert_key = /etc/kong/ssl/kong.key

# Logging
log_level = notice
proxy_access_log = /var/log/kong/access.log
proxy_error_log = /var/log/kong/error.log
admin_access_log = /var/log/kong/admin_access.log
admin_error_log = /var/log/kong/admin_error.log

# Performance
nginx_worker_processes = auto
upstream_keepalive_pool_size = 60
upstream_keepalive_max_requests = 100
upstream_keepalive_idle_timeout = 60

# Security
headers = off
trusted_ips = 0.0.0.0/0,::/0
real_ip_header = X-Forwarded-For
real_ip_recursive = on

# Plugins
plugins = bundled
KONGCONF

              # kong.yml - Configuración declarativa de servicios
              sudo tee /etc/kong/kong.yml > /dev/null <<KONGYML
_format_version: "3.0"
_transform: true

# ==========================================
# SERVICIOS
# ==========================================
services:

  # -----------------------------------------
  # Django API (via ALB interno)
  # -----------------------------------------
  - name: django-api
    url: https://$${ALB_DNS}
    protocol: https
    port: 443
    retries: 3
    connect_timeout: 10000
    write_timeout: 60000
    read_timeout: 60000
    
    routes:
      - name: api-route
        paths:
          - /api
        strip_path: false
        preserve_host: false
        
      - name: inventario-route
        paths:
          - /inventario
        strip_path: false
        preserve_host: false
        
      - name: admin-route
        paths:
          - /admin
        strip_path: false
        preserve_host: false
        
      - name: static-route
        paths:
          - /static
        strip_path: false
        preserve_host: false
    
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
          credentials: true
          max_age: 3600

  # -----------------------------------------
  # Notifications Microservice
  # -----------------------------------------
  - name: notifications-service
    url: http://${aws_instance.notifications.private_ip}:8001
    protocol: http
    port: 8001
    retries: 3
    connect_timeout: 10000
    write_timeout: 60000
    read_timeout: 60000
    
    routes:
      - name: notifications-route
        paths:
          - /notifications
        strip_path: true
        preserve_host: false
    
    plugins:
      - name: rate-limiting
        config:
          minute: 100
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
          credentials: true
          max_age: 3600

  # -----------------------------------------
  # Health Check interno
  # -----------------------------------------
  - name: kong-health-service
    url: http://127.0.0.1:8100/status
    routes:
      - name: health-route
        paths:
          - /health
          - /kong-health
        methods:
          - GET

# ==========================================
# PLUGINS GLOBALES
# ==========================================
plugins:
  - name: correlation-id
    config:
      header_name: X-Request-ID
      generator: uuid
      echo_downstream: true
      
  - name: file-log
    config:
      path: /var/log/kong/requests.log
      reopen: true
KONGYML

              # ==========================================
              # SERVICIO SYSTEMD
              # ==========================================
              echo "$$(date): Configurando servicio systemd..."
              
              sudo tee /etc/systemd/system/kong.service > /dev/null <<'SYSTEMD'
[Unit]
Description=Kong API Gateway
After=network.target
Wants=network-online.target

[Service]
Type=forking
User=root
ExecStartPre=/usr/local/bin/kong check /etc/kong/kong.conf
ExecStart=/usr/local/bin/kong start -c /etc/kong/kong.conf
ExecReload=/usr/local/bin/kong reload -c /etc/kong/kong.conf
ExecStop=/usr/local/bin/kong stop
Restart=always
RestartSec=5
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
SYSTEMD

              sudo systemctl daemon-reload
              
              # ==========================================
              # ESPERAR ALB E INICIAR KONG
              # ==========================================
              echo "$$(date): Esperando que el ALB esté disponible..."
              echo "$$(date): ALB DNS: $${ALB_DNS}"
              
              # Esperar hasta 10 minutos a que el ALB responda
              for i in {1..60}; do
                HTTP_CODE=$$(curl -sk -o /dev/null -w "%%{http_code}" "https://$${ALB_DNS}/inventario/" 2>/dev/null || echo "000")
                if [ "$$HTTP_CODE" = "200" ] || [ "$$HTTP_CODE" = "301" ] || [ "$$HTTP_CODE" = "302" ]; then
                  echo "$$(date): ✅ ALB respondiendo (HTTP $$HTTP_CODE)"
                  break
                fi
                echo "$$(date): Esperando ALB... intento $$i/60 (HTTP: $$HTTP_CODE)"
                sleep 10
              done
              
              # Verificar configuración
              echo "$$(date): Verificando configuración de Kong..."
              sudo /usr/local/bin/kong check /etc/kong/kong.conf
              
              # Iniciar Kong
              echo "$$(date): Iniciando Kong Gateway..."
              sudo /usr/local/bin/kong start -c /etc/kong/kong.conf
              
              # Habilitar inicio automático
              sudo systemctl enable kong
              
              # Verificar estado
              sleep 5
              sudo /usr/local/bin/kong health
              
              # ==========================================
              # RESUMEN
              # ==========================================
              PUBLIC_IP=$$(curl -sf http://169.254.169.254/latest/meta-data/public-ipv4 || echo "unknown")
              
              echo ""
              echo "=========================================="
              echo "✅ KONG API GATEWAY - INSTALACIÓN COMPLETA"
              echo "=========================================="
              echo ""
              echo "🌐 PUNTO DE ENTRADA ÚNICO (usar estas URLs):"
              echo "   HTTP:  http://$${PUBLIC_IP}:8000"
              echo "   HTTPS: https://$${PUBLIC_IP}:443"
              echo ""
              echo "📊 Health Check:"
              echo "   http://$${PUBLIC_IP}:8100/status"
              echo "   http://$${PUBLIC_IP}:8000/health"
              echo ""
              echo "🔗 Backend interno (ALB):"
              echo "   $${ALB_DNS}"
              echo ""
              echo "📝 Rutas disponibles:"
              echo "   /api/*           → Django API"
              echo "   /inventario/*    → Django Inventario"
              echo "   /admin/*         → Django Admin"
              echo "   /notifications/* → Notifications Microservice"
              echo "   /health          → Kong Health"
              echo ""
              echo "🔧 Comandos útiles:"
              echo "   sudo kong health"
              echo "   sudo kong reload"
              echo "   sudo tail -f /var/log/kong/access.log"
              echo "   cat /var/log/kong-install.log"
              echo "=========================================="
              
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-gateway"
    Role = "api-gateway"
  })

  depends_on = [aws_lb.main, aws_lb_listener.https, aws_instance.app_server, aws_instance.notifications]
}
