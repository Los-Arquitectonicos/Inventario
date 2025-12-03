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

# Provider para crear certificados SSL autofirmados
provider "tls" {
  # Configuration for generating self-signed certificates
}

locals {
  project_name = "${var.project_prefix}-wms"
  repository   = "https://github.com/Los-Arquitectonicos/Inventario.git"
  branch       = "servicediscovery"

  common_tags = {
    Project     = local.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Data Source: Obtener AMI más reciente de Ubuntu 24.04
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
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

# Security Group: ALB (Application Load Balancer) - INTERNO
# Solo Kong puede acceder al ALB
resource "aws_security_group" "alb" {
  name        = "${var.project_prefix}-alb-sg"
  description = "Security group for ALB - Internal use by Kong only"
  vpc_id      = data.aws_vpc.default.id

  # NOTA: El acceso desde Kong se agrega en kong.tf via aws_security_group_rule

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
  ami                         = data.aws_ami.ubuntu.id
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
              
              # Instalar PostgreSQL
              sudo apt-get install -y postgresql postgresql-contrib
              
              # Configurar PostgreSQL
              sudo -u postgres psql -c "CREATE USER ${var.database_user} WITH PASSWORD '${var.db_password}';"
              sudo -u postgres createdb -O ${var.database_user} ${var.database_name}
              sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${var.database_name} TO ${var.database_user};"
              
              # Configurar acceso remoto
              sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/16/main/postgresql.conf
              echo "host ${var.database_name} ${var.database_user} 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              echo "host all all 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              
              # Optimizar configuración
              sudo sed -i "s/max_connections = 100/max_connections = 200/g" /etc/postgresql/16/main/postgresql.conf
              sudo sed -i "s/#shared_buffers = 128MB/shared_buffers = 256MB/g" /etc/postgresql/16/main/postgresql.conf
              
              # Reiniciar PostgreSQL
              sudo systemctl restart postgresql
              sudo systemctl enable postgresql
              
              echo "Configuración de PostgreSQL completada"
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-database"
    Role = "database"
  })
}

# Instancias EC2: Servidores de aplicación Django con JWT
resource "aws_instance" "app_server" {
  count = var.app_server_count

  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true

  user_data = <<-EOT
    #!/bin/bash
    
    # Variables
    DATABASE_HOST="${aws_instance.database.private_ip}"
    
    # Persistir variables de entorno
    echo "DATABASE_HOST=${aws_instance.database.private_ip}" | sudo tee -a /etc/environment
    echo "DATABASE_NAME=${var.database_name}" | sudo tee -a /etc/environment
    echo "DATABASE_USER=${var.database_user}" | sudo tee -a /etc/environment
    echo "DATABASE_PASSWORD=${var.db_password}" | sudo tee -a /etc/environment
    echo "DATABASE_PORT=${var.database_port}" | sudo tee -a /etc/environment
    echo "SECRET_KEY=${var.django_secret_key}" | sudo tee -a /etc/environment
    echo "DEBUG=${var.debug_mode}" | sudo tee -a /etc/environment
    
    # Instalar dependencias
    sudo apt-get update -y
    sudo apt-get install -y python3-pip python3-venv git libpq-dev postgresql-client
    
    # Instalar Django globalmente
    sudo pip3 install --break-system-packages django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers gunicorn
    
    # Clonar repositorio
    cd /home/ubuntu
    git clone ${local.repository}
    cd Inventario
    git checkout ${local.branch}
    chown -R ubuntu:ubuntu /home/ubuntu/Inventario
    
    # Esperar base de datos
    sleep 30
    
    # Migraciones solo en servidor 1
    %{if count.index == 0}
    cd /home/ubuntu/Inventario/ProvesiWMS
    source /etc/environment
    python3 manage.py migrate --noinput || true
    python3 setup_users.py || true
    %{else}
    sleep 60
    %{endif}
    
    # Iniciar Django en background
    cd /home/ubuntu/Inventario/ProvesiWMS
    source /etc/environment
    nohup python3 manage.py runserver 0.0.0.0:8000 > /home/ubuntu/django.log 2>&1 &
    
    echo "Django started"
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
    timeout             = 10
    interval            = 30
    path                = "/inventario/"
    matcher             = "200,301,302"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-app-tg"
  })
}

# Registrar instancias en el Target Group
resource "aws_lb_target_group_attachment" "app" {
  count = var.app_server_count

  target_group_arn = aws_lb_target_group.app.arn
  target_id        = aws_instance.app_server[count.index].id
  port             = 8000
}

# ===========================
# CERTIFICADO SSL COMPATIBLE CON AWS ACADEMY
# ===========================
# Enfoque compatible que no requiere permisos IAM especiales

# Generar clave privada
resource "tls_private_key" "alb_private_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

# Generar certificado autofirmado
resource "tls_self_signed_cert" "alb_cert" {
  private_key_pem = tls_private_key.alb_private_key.private_key_pem

  subject {
    common_name  = "provesi.local"
    organization = "ProvesiWMS Development"
    country      = "US"
  }

  validity_period_hours = 8760 # 1 año

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]

  dns_names = [
    "provesi.local",
    "*.provesi.local",
    "localhost"
  ]
}

# Crear certificado en ACM (método compatible con AWS Academy)
resource "aws_acm_certificate" "alb_cert" {
  private_key      = tls_private_key.alb_private_key.private_key_pem
  certificate_body = tls_self_signed_cert.alb_cert.cert_pem

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-ssl-cert"
  })
}

# ===========================
# APPLICATION LOAD BALANCER
# ===========================

# ===========================
# LOAD BALANCER LISTENERS
# ===========================

# Listener HTTP (puerto 80) - Redirige a HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Listener HTTPS (puerto 443) - Endpoint principal
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.alb_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  depends_on = [aws_acm_certificate.alb_cert]
}

# ==========================================
# KONG API GATEWAY - SERVICE DISCOVERY
# ==========================================
# Los archivos de Kong están en terraform/kong/
# y se incluyen automáticamente por Terraform
# ==========================================
