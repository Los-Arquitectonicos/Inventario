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

  user_data = <<-EOT
              #!/bin/bash
              
              # Log de instalación
              exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
              echo "=========================================="
              echo "CONFIGURANDO SERVIDOR ${count.index + 1}"
              echo "$(date): Iniciando configuración..."
              echo "=========================================="
              
              # Configurar variables de entorno
              echo "$(date): Configurando variables de entorno..."
              ${local.env_script}
              source /etc/environment
              
              # Actualizar sistema e instalar dependencias
              echo "$(date): Instalando dependencias..."
              apt-get update -y
              apt-get install -y python3-pip git postgresql-client nginx build-essential libpq-dev python3-dev
              
              # Instalar Django (manejar entorno externamente administrado)
              echo "$(date): Instalando Django..."
              pip3 install --break-system-packages django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers gunicorn || \
              pip3 install django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers gunicorn
              
              # Verificar Django
              python3 -c "import django; print('Django OK')" || { echo "Django no instalado"; exit 1; }
              
              # Clonar repositorio
              echo "$(date): Clonando repositorio..."
              mkdir -p /opt/apps && cd /opt/apps
              rm -rf Inventario
              git clone ${local.repository}
              cd Inventario && git checkout ${local.branch} && cd ProvesiWMS
              
              # Verificar archivos
              [ ! -f manage.py ] && { echo "manage.py no encontrado"; exit 1; }
              
              # Esperar base de datos
              echo "$(date): Esperando base de datos..."
              for i in {1..30}; do
                pg_isready -h ${aws_instance.database.private_ip} -p ${var.database_port} -U ${var.database_user} && break
                sleep 10
              done
              
              # Migraciones (solo servidor 1)
              %{if count.index == 0}
              echo "$(date): Aplicando migraciones..."
              python3 manage.py makemigrations --noinput || true
              python3 manage.py migrate --noinput || true
              [ -f setup_users.py ] && python3 setup_users.py || true
              python3 manage.py collectstatic --noinput || true
              %{else}
              sleep 120
              %{endif}
              
              # Configurar Nginx
              echo "$(date): Configurando Nginx..."
              cat > /etc/nginx/sites-available/default << 'EOF'
              server {
                  listen 80;
                  location / {
                      proxy_pass http://127.0.0.1:8000;
                      proxy_set_header Host \$host;
                  }
                  location /static/ {
                      alias /opt/apps/Inventario/ProvesiWMS/static/;
                  }
              }
              EOF
              systemctl restart nginx
              
              # Script de inicio
              cat > /home/ubuntu/start-django.sh << 'EOF'
              #!/bin/bash
              cd /opt/apps/Inventario/ProvesiWMS
              source /etc/environment
              python3 manage.py runserver 0.0.0.0:8000
              EOF
              chmod +x /home/ubuntu/start-django.sh
              chown ubuntu:ubuntu /home/ubuntu/start-django.sh
              
              echo "$(date): ✅ CONFIGURACIÓN COMPLETADA - Servidor ${count.index + 1}"
              echo "Para iniciar: ./start-django.sh"
              
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

# Listener para el ALB (puerto 443 - HTTPS)
resource "aws_lb_listener" "https" {
  count = var.domain_name != "" && var.ssl_certificate_arn != "" ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# CloudWatch Log Groups (si están habilitados)
resource "aws_cloudwatch_log_group" "app_logs" {
  count = var.enable_cloudwatch_logs ? 1 : 0

  name              = "${local.project_name}-app-logs"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "nginx_logs" {
  count = var.enable_cloudwatch_logs ? 1 : 0

  name              = "${local.project_name}-nginx-logs"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "db_logs" {
  count = var.enable_cloudwatch_logs ? 1 : 0

  name              = "${local.project_name}-db-logs"
  retention_in_days = 7

  tags = local.common_tags
}

# Auto Scaling Group (opcional) - Simplificado
resource "aws_launch_template" "app" {
  count = var.enable_auto_scaling ? 1 : 0

  name_prefix   = "${var.project_prefix}-app-template-"
  image_id      = "ami-0e2c8caa4b6378d8c"
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.app.id]

  # User data inline (simplificado para Auto Scaling)
  user_data = base64encode(<<-EOT
    #!/bin/bash
    echo "Auto Scaling instance configuration..."
    # Configuración básica para Auto Scaling
    # Las configuraciones detalladas se aplicarán manualmente
    EOT
  )

  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${var.project_prefix}-app-server-asg"
    })
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "app" {
  count = var.enable_auto_scaling ? 1 : 0

  name                = "${var.project_prefix}-app-asg"
  vpc_zone_identifier = data.aws_subnets.available.ids
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"

  min_size         = var.min_servers
  max_size         = var.max_servers
  desired_capacity = var.desired_servers

  launch_template {
    id      = aws_launch_template.app[0].id
    version = "$Latest"
  }

  lifecycle {
    create_before_destroy = true
  }

  tag {
    key                 = "Name"
    value               = "${var.project_prefix}-app-asg"
    propagate_at_launch = true
  }

  dynamic "tag" {
    for_each = local.common_tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}