# ***************** ProvesiWMS - Deployment Simplificado ***********************
# Sistema de Inventario con Microservicios
#
# Elementos a desplegar:
# 1. Grupos de seguridad (HTTP, PostgreSQL, MongoDB, SSH)
# 2. Instancias EC2:
#    - provesi-db (PostgreSQL con Docker)
#    - provesi-mongodb (MongoDB con Docker)
#    - provesi-django (Django + repositorio descargado)
#    - provesi-notifications (FastAPI + repositorio descargado)
#    - provesi-kong (Kong API Gateway con Docker)
# ******************************************************************

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_prefix" {
  description = "Prefix used for naming AWS resources"
  type        = string
  default     = "provesi"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "SSH key pair name for EC2 instances"
  type        = string
  default     = "vockey"
}

provider "aws" {
  region = var.region
}

locals {
  project_name = "${var.project_prefix}-wms"
  repository   = "https://github.com/Los-Arquitectonicos/Inventario.git"
  branch       = "servicediscovery"

  common_tags = {
    Project   = local.project_name
    ManagedBy = "Terraform"
  }
}

# Data Source: VPC por defecto
data "aws_vpc" "default" {
  filter {
    name   = "isDefault"
    values = ["true"]
  }
}

# Data Source: Subnets disponibles
data "aws_subnets" "available" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# AMI de Amazon Linux 2023 (viene con Docker preinstalado)
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# AMI de Ubuntu 24.04 para Django/FastAPI
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

# Security Group: Kong (puerto 8000)
resource "aws_security_group" "traffic_kong" {
  name        = "${var.project_prefix}-traffic-kong"
  description = "Allow Kong traffic on ports 8000 (HTTP) and 8443 (HTTPS)"

  ingress {
    description = "Kong HTTP access"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kong HTTPS access"
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-kong"
  })
}

# Security Group: ALB (puerto 443 desde Kong)
resource "aws_security_group" "traffic_alb" {
  name        = "${var.project_prefix}-traffic-alb"
  description = "Allow ALB traffic from Kong"

  ingress {
    description = "HTTPS from Kong"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from Kong"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-alb"
  })
}

# Security Group: Django (puerto 8080 desde ALB)
resource "aws_security_group" "traffic_django" {
  name        = "${var.project_prefix}-traffic-django"
  description = "Allow Django traffic from ALB"

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.traffic_alb.id]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-django"
  })
}

# Security Group: FastAPI (puerto 8001)
resource "aws_security_group" "traffic_notifications" {
  name        = "${var.project_prefix}-traffic-notifications"
  description = "Allow FastAPI traffic on port 8001"

  ingress {
    description = "FastAPI HTTP access"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-notifications"
  })
}

# Security Group: PostgreSQL (puerto 5432)
resource "aws_security_group" "traffic_db" {
  name        = "${var.project_prefix}-traffic-db"
  description = "Allow PostgreSQL access"

  ingress {
    description = "PostgreSQL access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-db"
  })
}

# Security Group: MongoDB (puerto 27017)
resource "aws_security_group" "traffic_mongodb" {
  name        = "${var.project_prefix}-traffic-mongodb"
  description = "Allow MongoDB access"

  ingress {
    description = "MongoDB access"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-mongodb"
  })
}

# Security Group: SSH (puerto 22) + Egress
resource "aws_security_group" "traffic_ssh" {
  name        = "${var.project_prefix}-traffic-ssh"
  description = "Allow SSH access"

  ingress {
    description = "SSH access"
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
    Name = "${var.project_prefix}-traffic-ssh"
  })
}

# ====================================================================================
# INSTANCIAS EC2
# ====================================================================================

# Instancia: PostgreSQL con Docker
resource "aws_instance" "database" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_db.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              
              docker run --restart=always -d \
                -e POSTGRES_USER=provesi_user \
                -e POSTGRES_DB=provesi_wms \
                -e POSTGRES_PASSWORD=Provesi2024! \
                -p 5432:5432 \
                --name provesi-db postgres
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-db"
    Role = "database"
  })
}

# Instancia: MongoDB con Docker
resource "aws_instance" "mongodb" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_mongodb.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              
              docker run --restart=always -d \
                -p 27017:27017 \
                --name provesi-mongodb mongo
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-mongodb"
    Role = "mongodb"
  })
}

# Instancias: Django x2 (solo descarga, NO ejecuta)
resource "aws_instance" "django" {
  count                       = 2
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_django.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              
              export DATABASE_HOST=${aws_instance.database.private_ip}
              echo "DATABASE_HOST=${aws_instance.database.private_ip}" | sudo tee -a /etc/environment
              export DATABASE_NAME=provesi_wms
              echo "DATABASE_NAME=provesi_wms" | sudo tee -a /etc/environment
              export DATABASE_USER=provesi_user
              echo "DATABASE_USER=provesi_user" | sudo tee -a /etc/environment
              export DATABASE_PASSWORD='Provesi2024!'
              echo "DATABASE_PASSWORD='Provesi2024!'" | sudo tee -a /etc/environment
              export DATABASE_PORT=5432
              echo "DATABASE_PORT=5432" | sudo tee -a /etc/environment

              sudo apt-get update -y
              sudo apt-get install -y python3-pip python3-venv git libpq-dev python3-dev

              mkdir -p /home/ubuntu/app
              cd /home/ubuntu/app
              git clone -b ${local.branch} ${local.repository}
              cd Inventario/ProvesiWMS

              # Crear virtualenv e instalar dependencias
              python3 -m venv venv
              source venv/bin/activate
              pip install --upgrade pip setuptools wheel
              pip install -r requirements.txt
              
              # Cambiar ownership al usuario ubuntu
              sudo chown -R ubuntu:ubuntu /home/ubuntu/app
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-django-${count.index + 1}"
    Role = "django-app"
  })

  depends_on = [aws_instance.database]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.traffic_alb.id]
  subnets            = data.aws_subnets.available.ids

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-alb"
  })
}

# Target Group para Django
resource "aws_lb_target_group" "django" {
  name     = "${var.project_prefix}-django-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200,301,302"
    path                = "/inventario/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-django-tg"
  })
}

# Registrar instancias Django en el Target Group
resource "aws_lb_target_group_attachment" "django" {
  count            = 2
  target_group_arn = aws_lb_target_group.django.arn
  target_id        = aws_instance.django[count.index].id
  port             = 8080
}

# Certificado SSL Self-Signed para HTTPS
resource "tls_private_key" "alb_cert" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_self_signed_cert" "alb_cert" {
  private_key_pem = tls_private_key.alb_cert.private_key_pem

  subject {
    common_name  = aws_lb.main.dns_name
    organization = "Provesi WMS"
  }

  validity_period_hours = 8760 # 1 año

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

resource "aws_acm_certificate" "alb_cert" {
  private_key      = tls_private_key.alb_cert.private_key_pem
  certificate_body = tls_self_signed_cert.alb_cert.cert_pem

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-alb-cert"
  })
}

# Listener HTTP para el ALB (redirect a HTTPS)
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

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-listener-http"
  })
}

# Listener HTTPS para el ALB
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.alb_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.django.arn
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-listener-https"
  })
}

# Instancia: FastAPI Notifications (solo descarga, NO ejecuta)
resource "aws_instance" "notifications" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_notifications.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              
              export MONGODB_HOST=${aws_instance.mongodb.private_ip}
              echo "MONGODB_HOST=${aws_instance.mongodb.private_ip}" | sudo tee -a /etc/environment
              export MONGODB_PORT=27017
              echo "MONGODB_PORT=27017" | sudo tee -a /etc/environment
              export MONGODB_DATABASE=notifications_db
              echo "MONGODB_DATABASE=notifications_db" | sudo tee -a /etc/environment

              sudo apt-get update -y
              sudo apt-get install -y python3-pip python3-venv git

              mkdir -p /home/ubuntu/app
              cd /home/ubuntu/app
              git clone -b ${local.branch} ${local.repository}
              cd Inventario/notifications

              # Crear virtualenv e instalar dependencias
              python3 -m venv venv
              source venv/bin/activate
              pip install --upgrade pip setuptools wheel
              pip install -r requirements.txt
              
              # Cambiar ownership al usuario ubuntu
              sudo chown -R ubuntu:ubuntu /home/ubuntu/app
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-notifications"
    Role = "notifications-service"
  })

  depends_on = [aws_instance.mongodb]
}

# Instancia: Kong API Gateway con Docker
resource "aws_instance" "kong" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.traffic_kong.id, aws_security_group.traffic_ssh.id]

  user_data = <<-EOT
              #!/bin/bash
              exec > /var/log/kong-setup.log 2>&1
              set -x
              
              export ALB_DNS=${aws_lb.main.dns_name}
              echo "ALB_DNS=${aws_lb.main.dns_name}" | sudo tee -a /etc/environment
              
              export NOTIFICATIONS_HOST=${aws_instance.notifications.private_ip}
              echo "NOTIFICATIONS_HOST=${aws_instance.notifications.private_ip}" | sudo tee -a /etc/environment

              # Instalar git y openssl
              yum install -y git openssl

              mkdir -p /opt/kong/certs
              cd /opt/kong
              git clone -b ${local.branch} ${local.repository}
              cd Inventario

              # Configurar kong.yaml con el DNS del ALB y la IP de notifications
              sed -i "s/<DJANGO_HOST>/${aws_lb.main.dns_name}/g" kong.yaml
              sed -i "s/<NOTIFICATIONS_HOST>/${aws_instance.notifications.private_ip}/g" kong.yaml

              # Generar certificado SSL self-signed para Kong
              cd /opt/kong/certs
              openssl req -x509 -newkey rsa:2048 -nodes \
                -keyout kong-key.pem \
                -out kong-cert.pem \
                -days 365 \
                -subj "/CN=kong-gateway/O=Provesi WMS"

              # Crear network y ejecutar Kong con HTTPS
              docker network create kong-net 2>/dev/null || true
              docker run -d --name kong --network=kong-net --restart=always \
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
              
              echo "Kong setup completed at $(date)" >> /var/log/kong-setup.log
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong"
    Role = "api-gateway"
  })

  depends_on = [aws_instance.django, aws_instance.notifications]
}

# ====================================================================================
# OUTPUTS
# ====================================================================================

output "kong_public_ip" {
  description = "Kong API Gateway public IP"
  value       = aws_instance.kong.public_ip
}

output "django_public_ips" {
  description = "Django instances public IPs"
  value       = aws_instance.django[*].public_ip
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "notifications_public_ip" {
  description = "Notifications service public IP"
  value       = aws_instance.notifications.public_ip
}

output "database_private_ip" {
  description = "PostgreSQL database private IP"
  value       = aws_instance.database.private_ip
}

output "mongodb_private_ip" {
  description = "MongoDB private IP"
  value       = aws_instance.mongodb.private_ip
}

output "instructions" {
  description = "Next steps to run the applications"
  value       = <<-EOT
  
  ========================================
  DEPLOYMENT COMPLETADO
  ========================================
  
  Las aplicaciones están instaladas pero NO ejecutándose.
  Debes iniciarlas manualmente:
  
  1. DJANGO (conectar a ambas instancias):
     
     INSTANCIA 1:
     ssh ubuntu@${aws_instance.django[0].public_ip}
     cd /home/ubuntu/app/Inventario/ProvesiWMS
     source venv/bin/activate
     python3 manage.py migrate  # SOLO en la primera instancia
     python3 manage.py runserver 0.0.0.0:8080
     
     INSTANCIA 2:
     ssh ubuntu@${aws_instance.django[1].public_ip}
     cd /home/ubuntu/app/Inventario/ProvesiWMS
     source venv/bin/activate
     python3 manage.py runserver 0.0.0.0:8080
  
  2. NOTIFICATIONS:
     ssh ubuntu@${aws_instance.notifications.public_ip}
     cd /home/ubuntu/app/Inventario/notifications
     source venv/bin/activate
     python3 initialize_users.py  # SOLO la primera vez
     python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
  
  3. KONG API Gateway:
     Kong ya está ejecutándose en: http://${aws_instance.kong.public_ip}:8000
  
  4. VERIFICAR:
     # A través de Kong
     curl http://${aws_instance.kong.public_ip}:8000/inventario/
     
     # Directamente al ALB (opcional)
     curl http://${aws_lb.main.dns_name}/inventario/
  
  ========================================
  
  ARQUITECTURA:
  Internet → Kong (${aws_instance.kong.public_ip}:8000)
           ├→ /inventario, /api, /admin → ALB (${aws_lb.main.dns_name})
           │                               ├→ Django 1 (${aws_instance.django[0].private_ip}:8080)
           │                               └→ Django 2 (${aws_instance.django[1].private_ip}:8080)
           └→ /notifications → FastAPI (${aws_instance.notifications.private_ip}:8001)
  
  ========================================
  EOT
}
