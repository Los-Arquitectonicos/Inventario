# ***************** Inventario WMS - Deployment ***********************
# ****** Arquitectura y diseño de Software ******
#
# Infraestructura para ProvesiWMS en AWS (usando VPC por defecto)
#
# Elementos a desplegar:
# 1. Application Load Balancer
# 2. Grupos de seguridad:
#    - alb-traffic (puerto 80)
#    - app-traffic (puerto 8000)
#    - db-traffic (puerto 5432)
# 3. Instancias EC2:
#    - app-server-1 (Django en puerto 8000)
#    - app-server-2 (Django en puerto 8000)
#    - db-server (PostgreSQL)
# 4. Target Group para el ALB
# ******************************************************************

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
  description = "EC2 instance type for application servers"
  type        = string
  default     = "t2.small"
}

variable "db_instance_type" {
  description = "EC2 instance type for database server"
  type        = string
  default     = "t2.micro"
}

variable "db_password" {
  description = "Password for PostgreSQL database"
  type        = string
  default     = "inventario2024"
  sensitive   = true
}

provider "aws" {
  region = var.region
}

locals {
  project_name = "${var.project_prefix}-wms"
  repository   = "https://github.com/Los-Arquitectonicos/Inventario.git"
  branch       = "reescritura-completa"

  common_tags = {
    Project   = local.project_name
    ManagedBy = "Terraform"
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

# Data Source: Obtener VPC por defecto
data "aws_vpc" "default" {
  default = true
}

# Data Source: Obtener subnets por defecto
data "aws_subnets" "default" {
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
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.db_instance_type
  vpc_security_group_ids      = [aws_security_group.db.id]
  associate_public_ip_address = true

  user_data = <<-EOT
              #!/bin/bash
              
              # Actualizar sistema
              sudo apt-get update -y
              sudo apt-get upgrade -y
              
              # Instalar PostgreSQL
              sudo apt-get install -y postgresql postgresql-contrib
              
              # Configurar PostgreSQL
              sudo -u postgres psql -c "CREATE USER inventario_user WITH PASSWORD '${var.db_password}';"
              sudo -u postgres createdb -O inventario_user inventario_db
              
              # Permitir conexiones remotas
              echo "host all all 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              echo "listen_addresses='*'" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              echo "max_connections=500" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              
              # Reiniciar PostgreSQL
              sudo systemctl restart postgresql
              sudo systemctl enable postgresql
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-database"
    Role = "database"
  })
}

# Instancias EC2: Servidores de aplicación Django (2 instancias)
resource "aws_instance" "app_server" {
  count = 2

  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true

  user_data = <<-EOT
              #!/bin/bash
              
              # Variables de entorno
              export DATABASE_HOST=${aws_instance.database.private_ip}
              export DATABASE_NAME=inventario_db
              export DATABASE_USER=inventario_user
              export DATABASE_PASSWORD=${var.db_password}
              export DATABASE_PORT=5432
              
              # Persistir variables de entorno
              echo "DATABASE_HOST=${aws_instance.database.private_ip}" | sudo tee -a /etc/environment
              echo "DATABASE_NAME=inventario_db" | sudo tee -a /etc/environment
              echo "DATABASE_USER=inventario_user" | sudo tee -a /etc/environment
              echo "DATABASE_PASSWORD=${var.db_password}" | sudo tee -a /etc/environment
              echo "DATABASE_PORT=5432" | sudo tee -a /etc/environment
              
              # Actualizar sistema
              sudo apt-get update -y
              sudo apt-get upgrade -y
              
              # Instalar dependencias
              sudo apt-get install -y python3-pip python3-venv git build-essential libpq-dev python3-dev
              
              # Clonar repositorio
              mkdir -p /opt/apps
              cd /opt/apps
              
              if [ ! -d Inventario ]; then
                git clone ${local.repository}
              fi
              
              cd Inventario
              git fetch origin ${local.branch}
              git checkout ${local.branch}
              
              # Crear entorno virtual
              python3 -m venv venv
              source venv/bin/activate
              
              # Instalar dependencias Python
              pip install --upgrade pip
              pip install django psycopg2-binary gunicorn
              
              # Navegar al proyecto Django
              cd ProvesiWMS
              
              # Aplicar migraciones solo en la primera instancia
              if [ ${count.index} -eq 0 ]; then
                sleep 30  # Esperar a que la DB esté lista
                python manage.py makemigrations
                python manage.py migrate
              else
                sleep 60  # Esperar a que la primera instancia haga las migraciones
              fi
              
              # Crear script de inicio
              cat > /opt/apps/start_server.sh << 'EOF'
              #!/bin/bash
              source /etc/environment
              cd /opt/apps/Inventario/ProvesiWMS
              source ../venv/bin/activate
              gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 wms.wsgi:application
              EOF
              
              chmod +x /opt/apps/start_server.sh
              
              # Crear servicio systemd
              cat > /etc/systemd/system/provesi-wms.service << 'EOF'
              [Unit]
              Description=Provesi WMS Django Application
              After=network.target
              
              [Service]
              Type=simple
              User=ubuntu
              WorkingDirectory=/opt/apps/Inventario/ProvesiWMS
              Environment="PATH=/opt/apps/Inventario/venv/bin"
              EnvironmentFile=/etc/environment
              ExecStart=/opt/apps/start_server.sh
              Restart=always
              RestartSec=10
              
              [Install]
              WantedBy=multi-user.target
              EOF
              
              # Iniciar servicio
              sudo systemctl daemon-reload
              sudo systemctl enable provesi-wms
              sudo systemctl start provesi-wms
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
  subnets            = data.aws_subnets.default.ids

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

# Outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "URL to access the application through the ALB"
  value       = "http://${aws_lb.main.dns_name}/inventario/"
}

output "app_server_1_public_ip" {
  description = "Public IP of application server 1"
  value       = aws_instance.app_server[0].public_ip
}

output "app_server_2_public_ip" {
  description = "Public IP of application server 2"
  value       = aws_instance.app_server[1].public_ip
}

output "database_private_ip" {
  description = "Private IP of the PostgreSQL database"
  value       = aws_instance.database.private_ip
}

output "ssh_commands" {
  description = "SSH commands to connect to each server"
  value = {
    app_server_1 = "ssh ubuntu@${aws_instance.app_server[0].public_ip}"
    app_server_2 = "ssh ubuntu@${aws_instance.app_server[1].public_ip}"
  }
}
