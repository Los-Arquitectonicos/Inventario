# ***************** ProvesiWMS - Deployment con Autenticación ***********************
# ****** Sistema de Inventario con Seguridad JWT + HTTPS ******
#
# Infraestructura para ProvesiWMS en AWS con configuraciones de seguridad
#
# Elementos a desplegar:
# 1. Application Load Balancer con HTTPS
# 2. Grupos de seguridad optimizados
# 3. Instancias EC2 con variables de entorno de seguridad
# 4. Base de datos PostgreSQL configurada
# 5. CloudWatch Logs para monitoreo
# 6. Auto Scaling (opcional)
# 7. Certificado SSL (opcional)
# ******************************************************************

provider "aws" {
  region = var.region
}

locals {
  project_name = "${var.project_prefix}-wms"
  repository   = "https://github.com/Los-Arquitectonicos/Inventario.git"
  branch       = "Sprint3V2"  # Updated branch name

  # Variables de entorno para la aplicación Django
  django_env_vars = {
    # Database configuration
    DATABASE_HOST     = aws_instance.database.private_ip
    DATABASE_NAME     = var.database_name
    DATABASE_USER     = var.database_user
    DATABASE_PASSWORD = var.db_password
    DATABASE_PORT     = tostring(var.database_port)
    
    # Django core settings
    SECRET_KEY        = var.django_secret_key
    DEBUG             = tostring(var.debug_mode)
    ENVIRONMENT       = var.environment
    
    # HTTPS and security settings
    SECURE_SSL_REDIRECT              = var.environment == "production" ? "True" : "False"
    SECURE_PROXY_SSL_HEADER          = "HTTP_X_FORWARDED_PROTO,https"
    SESSION_COOKIE_SECURE            = var.environment == "production" ? "True" : "False"
    CSRF_COOKIE_SECURE               = var.environment == "production" ? "True" : "False"
    SECURE_HSTS_SECONDS              = var.environment == "production" ? "31536000" : "0"
    SECURE_HSTS_INCLUDE_SUBDOMAINS   = var.environment == "production" ? "True" : "False"
    SECURE_HSTS_PRELOAD              = var.environment == "production" ? "True" : "False"
    
    # JWT configuration
    JWT_ACCESS_TOKEN_LIFETIME_HOURS  = tostring(var.jwt_access_token_lifetime_hours)
    JWT_REFRESH_TOKEN_LIFETIME_DAYS  = tostring(var.jwt_refresh_token_lifetime_days)
    
    # Django allowed hosts
    DJANGO_ALLOWED_HOSTS = join(",", concat(var.allowed_hosts, [
      aws_lb.main.dns_name,
      var.domain_name != "" ? var.domain_name : ""
    ]))
    
    # CORS settings
    CORS_ALLOWED_ORIGINS = join(",", var.cors_allowed_origins)
    
    # Application settings
    GUNICORN_WORKERS = tostring(var.gunicorn_workers)
  }

  # Script de variables de entorno para user_data
  env_script = join("\n", [
    for key, value in local.django_env_vars :
    value != "" ? "echo '${key}=${value}' | sudo tee -a /etc/environment" : ""
    if value != ""
  ])

  common_tags = {
    Project     = local.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Data Source: Obtener VPC por defecto (compatible con AWS Academy)
data "aws_vpc" "default" {
  filter {
    name   = "isDefault"
    values = ["true"]
  }
}

# Data Source: Obtener subnets disponibles
data "aws_subnets" "available" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security Group: ALB (Application Load Balancer)
resource "aws_security_group" "alb" {
  name        = "${var.project_prefix}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-alb-sg"
  })
}

# Security Group: Servidores de aplicación Django
resource "aws_security_group" "app" {
  name        = "${var.project_prefix}-app-sg"
  description = "Security group for Django application servers"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Django from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-app-sg"
  })
}

# Security Group: Base de datos PostgreSQL
resource "aws_security_group" "db" {
  name        = "${var.project_prefix}-db-sg"
  description = "Security group for PostgreSQL database"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "PostgreSQL from app servers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-db-sg"
  })
}

# Instancia EC2: Base de datos PostgreSQL
resource "aws_instance" "database" {
  ami                         = "ami-0e2c8caa4b6378d8c"  # Ubuntu 24.04 LTS us-east-1
  instance_type               = var.db_instance_type
  vpc_security_group_ids      = [aws_security_group.db.id]
  associate_public_ip_address = true

  user_data = <<-EOT
              #!/bin/bash
              
              # Log de instalación
              exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
              echo "Iniciando configuración de base de datos PostgreSQL..."
              
              # Actualizar sistema
              sudo apt-get update -y
              sudo apt-get upgrade -y
              
              # Instalar PostgreSQL 16
              sudo apt-get install -y wget ca-certificates
              wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
              echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
              sudo apt-get update -y
              sudo apt-get install -y postgresql-16 postgresql-contrib-16
              
              # Configurar PostgreSQL
              sudo -u postgres psql -c "CREATE USER ${var.database_user} WITH PASSWORD '${var.db_password}';"
              sudo -u postgres createdb -O ${var.database_user} ${var.database_name}
              sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${var.database_name} TO ${var.database_user};"
              
              # Configurar acceso remoto
              sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/16/main/postgresql.conf
              echo "host ${var.database_name} ${var.database_user} 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              echo "host all all 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              
              # Optimizar configuración para producción
              sudo sed -i "s/max_connections = 100/max_connections = 200/g" /etc/postgresql/16/main/postgresql.conf
              sudo sed -i "s/#shared_buffers = 128MB/shared_buffers = 256MB/g" /etc/postgresql/16/main/postgresql.conf
              sudo sed -i "s/#effective_cache_size = 4GB/effective_cache_size = 1GB/g" /etc/postgresql/16/main/postgresql.conf
              
              # Reiniciar PostgreSQL
              sudo systemctl restart postgresql
              sudo systemctl enable postgresql
              
              # Instalar CloudWatch Agent (si está habilitado)
              %{if var.enable_cloudwatch_logs}
              wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
              sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
              
              # Configurar CloudWatch Agent
              sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null <<'EOF'
              {
                "logs": {
                  "logs_collected": {
                    "files": {
                      "collect_list": [
                        {
                          "file_path": "/var/log/postgresql/postgresql-16-main.log",
                          "log_group_name": "${local.project_name}-db-logs",
                          "log_stream_name": "{instance_id}"
                        }
                      ]
                    }
                  }
                }
              }
              EOF
              
              sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
              %{endif}
              
              echo "Configuración de PostgreSQL completada"
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-database"
    Role = "database"
  })
}

# Instancias EC2: Servidores de aplicación Django con autenticación JWT
resource "aws_instance" "app_server" {
  count = var.app_server_count

  ami                         = "ami-0e2c8caa4b6378d8c"  # Ubuntu 24.04 LTS us-east-1
  instance_type               = var.instance_type
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data_app.sh", {
    SERVER_INDEX = count.index + 1
    DATABASE_HOST_PLACEHOLDER = aws_instance.database.private_ip
  })
              #!/bin/bash
              
              # Log de instalación
              exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
              echo "Iniciando configuración de servidor de aplicación ${count.index + 1}..."
              
              # ===================================
              # CONFIGURAR VARIABLES DE ENTORNO
              # ===================================
              
              echo "Configurando variables de entorno de seguridad..."
              
              # Variables de entorno para Django y autenticación
              ${local.env_script}
              
              # Recargar variables de entorno
              source /etc/environment
              
              # ===================================
              # INSTALAR DEPENDENCIAS DEL SISTEMA
              # ===================================
              
              echo "Actualizando sistema e instalando dependencias..."
              
              # Actualizar sistema
              sudo apt-get update -y
              sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
              
              # Instalar dependencias base
              sudo apt-get install -y \
                python3-pip \
                python3-venv \
                git \
                build-essential \
                libpq-dev \
                python3-dev \
                nginx \
                supervisor \
                curl \
                wget \
                unzip \
                htop \
                postgresql-client
              
              # ===================================
              # CONFIGURAR APLICACIÓN DJANGO
              # ===================================
              
              echo "Configurando aplicación Django ProvesiWMS..."
              
              # Crear directorio de aplicaciones
              sudo mkdir -p /opt/apps
              sudo chown ubuntu:ubuntu /opt/apps
              cd /opt/apps
              
              # Clonar repositorio
              if [ ! -d Inventario ]; then
                echo "Clonando repositorio..."
                git clone ${local.repository}
              fi
              
              cd Inventario
              echo "Cambiando a branch ${local.branch}..."
              git fetch origin ${local.branch}
              git checkout ${local.branch}
              git pull origin ${local.branch}
              
              # Crear entorno virtual
              echo "Creando entorno virtual Python..."
              python3 -m venv venv
              source venv/bin/activate
              
              # Actualizar pip
              pip install --upgrade pip
              
              # Navegar al proyecto Django
              cd ProvesiWMS
              
              # Instalar dependencias Python
              echo "Instalando dependencias de Python..."
              if [ -f requirements.txt ]; then
                pip install -r requirements.txt
              else
                # Instalar dependencias mínimas si no existe requirements.txt
                pip install django psycopg2-binary gunicorn djangorestframework djangorestframework-simplejwt
              fi
              
              # ===================================
              # CONFIGURAR BASE DE DATOS
              # ===================================
              
              echo "Esperando a que la base de datos esté lista..."
              
              # Esperar a que PostgreSQL esté disponible
              while ! pg_isready -h ${aws_instance.database.private_ip} -p ${var.database_port} -U ${var.database_user}; do
                echo "Esperando conexión a PostgreSQL..."
                sleep 10
              done
              
              echo "Base de datos disponible, aplicando migraciones..."
              
              # Aplicar migraciones (solo en la primera instancia)
              %{if count.index == 0}
              echo "Aplicando migraciones en instancia principal..."
              python manage.py makemigrations --noinput
              python manage.py migrate --noinput
              
              # Ejecutar script de configuración de usuarios
              if [ -f setup_users.py ]; then
                echo "Configurando usuarios iniciales..."
                python setup_users.py
              fi
              
              # Recolectar archivos estáticos
              echo "Recolectando archivos estáticos..."
              python manage.py collectstatic --noinput
              %{else}
              echo "Esperando a que la instancia principal complete las migraciones..."
              sleep 120
              %{endif}
              
              # ===================================
              # CONFIGURAR GUNICORN
              # ===================================
              
              echo "Configurando Gunicorn..."
              
              # Crear configuración de Gunicorn
              cat > /opt/apps/Inventario/ProvesiWMS/gunicorn.conf.py << 'EOF'
              import multiprocessing
              import os
              
              # Server socket
              bind = "0.0.0.0:8000"
              backlog = 2048
              
              # Worker processes
              workers = int(os.environ.get('GUNICORN_WORKERS', ${var.gunicorn_workers}))
              worker_class = "sync"
              worker_connections = 1000
              timeout = 120
              keepalive = 2
              
              # Restart workers after this many requests, to control memory leaks
              max_requests = 1000
              max_requests_jitter = 50
              
              # Logging
              accesslog = "/var/log/gunicorn/access.log"
              errorlog = "/var/log/gunicorn/error.log"
              loglevel = "info"
              
              # Process naming
              proc_name = "provesi-wms"
              
              # Security
              limit_request_line = 4094
              limit_request_fields = 100
              limit_request_field_size = 8190
              EOF
              
              # Crear directorios de logs
              sudo mkdir -p /var/log/gunicorn
              sudo chown ubuntu:ubuntu /var/log/gunicorn
              
              # ===================================
              # PREPARAR ENTORNO PARA INICIO MANUAL
              # ===================================
              
              echo "Preparando entorno para inicio manual del servidor Django..."
              
              # Crear script de inicio manual
              cat > /opt/apps/Inventario/start_django.sh << 'EOF'
              #!/bin/bash
              echo "Iniciando ProvesiWMS..."
              cd /opt/apps/Inventario/ProvesiWMS
              source ../venv/bin/activate
              source /etc/environment
              sudo python3 manage.py runserver 0.0.0.0:8080
              EOF
              
              chmod +x /opt/apps/Inventario/start_django.sh
              
              # Crear script de verificación
              cat > /opt/apps/Inventario/check_status.sh << 'EOF'
              #!/bin/bash
              echo "=== Estado de ProvesiWMS ==="
              echo "Fecha: $(date)"
              echo ""
              echo "=== Variables de entorno ==="
              env | grep -E "DATABASE_|SECRET_KEY|DEBUG|ENVIRONMENT" | sort
              echo ""
              echo "=== Procesos Django ==="
              ps aux | grep "manage.py runserver" | grep -v grep
              echo ""
              echo "=== Test de conectividad a BD ==="
              pg_isready -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER
              EOF
              
              chmod +x /opt/apps/Inventario/check_status.sh
              
              # ===================================
              # CONFIGURAR CLOUDWATCH LOGS
              # ===================================
              
              %{if var.enable_cloudwatch_logs}
              echo "Configurando CloudWatch Logs..."
              
              # Instalar CloudWatch Agent
              wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
              sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
              
              # Configurar CloudWatch Agent
              sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null <<'EOF'
              {
                "logs": {
                  "logs_collected": {
                    "files": {
                      "collect_list": [
                        {
                          "file_path": "/var/log/gunicorn/error.log",
                          "log_group_name": "${local.project_name}-app-logs",
                          "log_stream_name": "app-server-${count.index + 1}-error"
                        },
                        {
                          "file_path": "/var/log/gunicorn/access.log",
                          "log_group_name": "${local.project_name}-app-logs",
                          "log_stream_name": "app-server-${count.index + 1}-access"
                        },
                        {
                          "file_path": "/var/log/supervisor/provesi-wms.log",
                          "log_group_name": "${local.project_name}-app-logs",
                          "log_stream_name": "app-server-${count.index + 1}-supervisor"
                        }
                      ]
                    }
                  }
                }
              }
              EOF
              
              sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
              %{endif}
              
              # ===================================
              # CONFIGURAR NGINX PARA DESARROLLO
              # ===================================
              
              echo "Configurando Nginx para desarrollo..."
              
              sudo tee /etc/nginx/sites-available/provesi-wms > /dev/null <<'EOF'
              server {
                  listen 80;
                  server_name _;
                  
                  client_max_body_size 100M;
                  
                  location / {
                      proxy_pass http://127.0.0.1:8080;
                      proxy_set_header Host $host;
                      proxy_set_header X-Real-IP $remote_addr;
                      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                      proxy_set_header X-Forwarded-Proto $scheme;
                      proxy_connect_timeout 600;
                      proxy_send_timeout 600;
                      proxy_read_timeout 600;
                      send_timeout 600;
                  }
                  
                  location /static/ {
                      alias /opt/apps/Inventario/ProvesiWMS/staticfiles/;
                      expires 1y;
                      add_header Cache-Control "public, immutable";
                  }
                  
                  location /health {
                      return 200 "healthy - manual start required\n";
                      add_header Content-Type text/plain;
                  }
              }
              EOF
              
              # Habilitar sitio
              sudo ln -sf /etc/nginx/sites-available/provesi-wms /etc/nginx/sites-enabled/
              sudo rm -f /etc/nginx/sites-enabled/default
              
              # Reiniciar Nginx
              sudo systemctl restart nginx
              sudo systemctl enable nginx
              
              # ===================================
              # FINALIZAR CONFIGURACIÓN
              # ===================================
              
              echo "Verificando estado de servicios..."
              sudo systemctl status nginx --no-pager
              
              echo "Configuración del servidor de aplicación completada"
              echo ""
              echo "============================================================="
              echo "SERVIDOR LISTO PARA INICIO MANUAL"
              echo "============================================================="
              echo "Para iniciar el servidor Django:"
              echo "1. ssh -i tu-clave.pem ubuntu@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
              echo "2. cd /opt/apps/Inventario/ProvesiWMS"
              echo "3. source ../venv/bin/activate"
              echo "4. sudo python3 manage.py runserver 0.0.0.0:8080"
              echo ""
              echo "Scripts disponibles:"
              echo "- /opt/apps/Inventario/start_django.sh (iniciar servidor)"
              echo "- /opt/apps/Inventario/check_status.sh (verificar estado)"
              echo "============================================================="
              
              echo "Configuración completa del servidor ${count.index + 1}"
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-app-server-${count.index + 1}"
    Role = "application"
  })

  depends_on = [aws_instance.database]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.available.ids

  enable_deletion_protection = false

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-alb"
  })
}

# Target Group para las instancias de aplicación
resource "aws_lb_target_group" "app" {
  name     = "${var.project_prefix}-app-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/inventario/"
    matcher             = "200,301,302"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-app-tg"
  })
}

# Registrar instancias en el Target Group
resource "aws_lb_target_group_attachment" "app" {
  count = 2

  target_group_arn = aws_lb_target_group.app.arn
  target_id        = aws_instance.app_server[count.index].id
  port             = 8000
}

# Listener para el ALB (puerto 80)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
